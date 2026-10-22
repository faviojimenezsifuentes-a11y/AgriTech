"""Entrena YOLO26 con aumentos moderados y evalúa fotos externas reservadas."""

from __future__ import annotations

import json
import time
import csv
from collections import defaultdict
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "training_data" / "semisupervised_v2"
OUTPUT = ROOT / "training_runs" / "yolo26n_semisupervised_v3"
BASELINE = ROOT / "models" / "esparragos_yolov8n_v2.pt"
INITIAL = ROOT / "models" / "esparragos_yolo26n_experimental.pt"


def evaluate_external(model_path: Path, holdout: list[dict]) -> dict:
    model = YOLO(str(model_path))
    results = []
    for row in holdout:
        source = ROOT / "dataset_candidates" / "inaturalist" / row["image_file"]
        start = time.perf_counter()
        prediction = model.predict(str(source), conf=0.25, imgsz=512, verbose=False)[0]
        duration_ms = (time.perf_counter() - start) * 1000
        predicted = [int(box.cls.item()) for box in prediction.boxes]
        results.append({"image_file": row["image_file"], "expected_class": row["class_id"],
                        "predicted_classes": predicted, "hit": row["class_id"] in predicted,
                        "other_class_boxes": sum(c != row["class_id"] for c in predicted),
                        "inference_ms": round(duration_ms, 1)})
    by_class: dict[str, dict] = defaultdict(lambda: {"hits": 0, "total": 0})
    for row in results:
        key = str(row["expected_class"])
        by_class[key]["total"] += 1
        by_class[key]["hits"] += row["hit"]
    return {"model": str(model_path), "hit_count": sum(row["hit"] for row in results),
            "total": len(results), "other_class_boxes": sum(row["other_class_boxes"] for row in results),
            "median_inference_ms": sorted(row["inference_ms"] for row in results)[len(results)//2],
            "by_class": dict(by_class), "details": results}


def evaluate_asparagus_context(model_path: Path) -> dict:
    directory = ROOT / "dataset_candidates" / "asparagus_context"
    if not (directory / "manifest.csv").is_file():
        return {"available": False}
    with (directory / "manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    model = YOLO(str(model_path))
    detected = []
    for row in rows:
        result = model.predict(str(directory / row["image_file"]), conf=0.25, imgsz=512, verbose=False)[0]
        detected.append({"image_file": row["image_file"], "boxes": len(result.boxes),
                         "classes": [int(box.cls.item()) for box in result.boxes]})
    return {"available": True, "images": len(rows),
            "images_with_boxes": sum(item["boxes"] > 0 for item in detected),
            "boxes": sum(item["boxes"] for item in detected), "details": detected,
            "warning": "Fotos de espárrago sin revisión de plagas; una caja aquí no demuestra un falso positivo."}


def main() -> None:
    provenance = json.loads((DATASET / "provenance.json").read_text(encoding="utf-8"))
    if len(provenance["holdout"]) != 32 or provenance["external_pseudo_labeled"] != 44:
        raise RuntimeError("La partición externa cambió; revisar antes de entrenar")
    training = YOLO(str(INITIAL)).train(
        data=str(DATASET / "data.yaml"), epochs=15, patience=6, imgsz=512,
        batch=8, device="cpu", workers=0, optimizer="AdamW", lr0=0.0005,
        mosaic=0.5, mixup=0.0, copy_paste=0.0, close_mosaic=8,
        project=str(ROOT / "training_runs"), name="yolo26n_semisupervised_v3",
        exist_ok=False, plots=False, save_period=5, seed=20261013,
    )
    best = Path(training.save_dir) / "weights" / "best.pt"
    report = {
        "evaluation": "Presencia de la clase esperada en 32 fotos externas reservadas; sin cajas verificadas, no es mAP ni precisión de campo.",
        "settings": {"initial_weights": str(INITIAL), "epochs_max": 15, "imgsz": 512, "optimizer": "AdamW", "lr0": 0.0005,
                     "mosaic": 0.5, "external_pseudo_labeled": 44},
        "baseline": evaluate_external(BASELINE, provenance["holdout"]),
        "candidate": evaluate_external(best, provenance["holdout"]),
        "asparagus_context": {"baseline": evaluate_asparagus_context(BASELINE),
                              "candidate": evaluate_asparagus_context(best)},
    }
    output = Path(training.save_dir) / "external_holdout_comparison.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({name: {key: data[key] for key in ("hit_count", "total", "other_class_boxes", "median_inference_ms")}
                      for name, data in report.items() if name in ("baseline", "candidate")}, indent=2))
    print(f"Reporte: {output}")


if __name__ == "__main__":
    main()

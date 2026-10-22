"""Compara coincidencia de clase en fotos nuevas; NO calcula mAP ni precisión.

La observación de iNaturalist no incluye cajas y puede contener otros insectos.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dataset_candidates" / "inaturalist"
BASELINE = ROOT / "models" / "esparragos_yolov8n_v2.pt"
CANDIDATE = ROOT / "runs" / "detect" / "training_runs" / "yolo26n_roboflow_v1_pilot" / "weights" / "best.pt"


def evaluate(path: Path, rows: list[dict]) -> dict:
    model = YOLO(str(path))
    hits = Counter()
    totals = Counter()
    false_classes = Counter()
    details = []
    for row in rows:
        expected = int(row["class_id"])
        results = model.predict(str(DATA / row["image_file"]), imgsz=512, conf=0.25, verbose=False)[0]
        detected = [int(box.cls.item()) for box in results.boxes]
        totals[expected] += 1
        hit = expected in detected
        hits[expected] += hit
        false_classes.update(c for c in detected if c != expected)
        details.append({"image_file": row["image_file"], "expected_class": expected,
                        "detected_classes": detected, "matching_class_seen": hit})
    return {"model": str(path), "overall_hit_rate": sum(hits.values()) / sum(totals.values()),
            "hits_by_class": {str(k): {"hits": hits[k], "total": totals[k]} for k in sorted(totals)},
            "other_class_predictions": dict(false_classes), "details": details,
            "limitation": "No box ground truth; cannot compute detection precision, recall, or mAP. Asparagus host unverified."}


def main() -> None:
    with (DATA / "manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not CANDIDATE.is_file():
        raise SystemExit(f"Falta el modelo entrenado: {CANDIDATE}")
    report = {"yolov8n_v2": evaluate(BASELINE, rows), "yolo26n_pilot": evaluate(CANDIDATE, rows)}
    out = ROOT / "training_runs" / "inat_weak_comparison.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: {kk: vv for kk, vv in value.items() if kk != "details"}
                      for k, value in report.items()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

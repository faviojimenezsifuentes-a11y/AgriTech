"""Valida una sola vez el umbral elegido en las 32 fotos externas reservadas."""

from __future__ import annotations

import json
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
PROVENANCE = ROOT / "training_data" / "semisupervised_v2" / "provenance.json"
OUTPUT = ROOT / "training_runs" / "confidence_holdout_validation.json"


def main() -> None:
    if OUTPUT.exists():
        raise RuntimeError("La prueba reservada ya se evaluó; no se repetirá para ajustar umbrales")
    holdout = json.loads(PROVENANCE.read_text(encoding="utf-8"))["holdout"]
    model = YOLO(str(ROOT / "models" / "esparragos_yolov8n_v2.pt"))
    report = {"method": "Umbral 0.30 elegido solo con desarrollo; evaluación reservada a 640 px, sin cajas verificadas.",
              "thresholds": {"0.30": {"hits": 0, "other_class_boxes": 0},
                             "0.45": {"hits": 0, "other_class_boxes": 0}},
              "images": len(holdout)}
    for row in holdout:
        image = ROOT / "dataset_candidates" / "inaturalist" / row["image_file"]
        prediction = model.predict(str(image), conf=0.10, imgsz=640, verbose=False)[0]
        for label, threshold in (("0.30", 0.30), ("0.45", 0.45)):
            classes = [int(box.cls.item()) for box in prediction.boxes if float(box.conf.item()) >= threshold]
            report["thresholds"][label]["hits"] += row["class_id"] in classes
            report["thresholds"][label]["other_class_boxes"] += sum(c != row["class_id"] for c in classes)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

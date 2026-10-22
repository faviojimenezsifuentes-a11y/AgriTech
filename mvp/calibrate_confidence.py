"""Evalúa umbrales de V2 en fotos externas de desarrollo, nunca en la prueba reservada."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "dataset_candidates" / "inaturalist"
PROVENANCE = ROOT / "training_data" / "semisupervised_v2" / "provenance.json"
OUTPUT = ROOT / "training_runs" / "confidence_development.json"
THRESHOLDS = (0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)


def main() -> None:
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    holdout = {row["image_file"] for row in provenance["holdout"]}
    with (CANDIDATES / "manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        development = [row for row in csv.DictReader(handle) if row["image_file"] not in holdout]
    if len(development) != 64:
        raise RuntimeError("La calibración debe usar exactamente las 64 fotos de desarrollo")
    model = YOLO(str(ROOT / "models" / "esparragos_yolov8n_v2.pt"))
    observations = []
    for row in development:
        result = model.predict(str(CANDIDATES / row["image_file"]), conf=0.10, imgsz=640, verbose=False)[0]
        observations.append({"expected": int(row["class_id"]),
                             "boxes": [(int(box.cls.item()), float(box.conf.item())) for box in result.boxes]})
    report = {}
    for threshold in THRESHOLDS:
        hits = 0
        other_boxes = 0
        by_class = defaultdict(lambda: {"hits": 0, "total": 0})
        for observation in observations:
            selected = [class_id for class_id, conf in observation["boxes"] if conf >= threshold]
            expected = observation["expected"]
            hit = expected in selected
            hits += hit
            other_boxes += sum(class_id != expected for class_id in selected)
            by_class[str(expected)]["total"] += 1
            by_class[str(expected)]["hits"] += hit
        report[str(threshold)] = {"expected_class_hits": hits, "total": len(observations),
                                  "other_class_boxes": other_boxes, "by_class": dict(by_class)}
    OUTPUT.write_text(json.dumps({"method": "Desarrollo: 64 fotos externas conocidas, nunca las 32 reservadas. Sin cajas verificadas.",
                                  "thresholds": report}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

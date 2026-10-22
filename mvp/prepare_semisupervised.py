"""Prepara un experimento con pseudoetiquetas, sin confundirlas con revisión humana."""

from __future__ import annotations

import csv
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from PIL import Image
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "training_data" / "roboflow_v1_grouped"
CANDIDATES = ROOT / "dataset_candidates" / "inaturalist"
DEST = ROOT / "training_data" / "semisupervised_v1"
TEACHER = ROOT / "models" / "esparragos_yolov8n_v2.pt"
SEED = 20261013


def copy_split(split: str) -> None:
    for kind in ("images", "labels"):
        target = DEST / split / kind
        target.mkdir(parents=True, exist_ok=True)
        for source in (SOURCE / split / kind).glob("*"):
            if source.is_file() and source.suffix.lower() != ".cache":
                shutil.copy2(source, target / source.name)


def main() -> None:
    if DEST.exists():
        raise RuntimeError(f"La salida ya existe; no se sobreescribirá: {DEST}")
    for split in ("train", "val", "test"):
        copy_split(split)
    with (CANDIDATES / "manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_class: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_class[int(row["class_id"])].append(row)
    rng = random.Random(SEED)
    train, holdout = [], []
    for class_id, items in sorted(by_class.items()):
        rng.shuffle(items)
        holdout_size = 2 if len(items) < 10 else 6
        holdout.extend(items[:holdout_size])
        train.extend(items[holdout_size:])
    train.sort(key=lambda row: row["image_file"])
    holdout.sort(key=lambda row: row["image_file"])
    if {r["observation_id"] for r in train} & {r["observation_id"] for r in holdout}:
        raise RuntimeError("Se repite una observación entre entrenamiento y prueba externa")

    model = YOLO(str(TEACHER))
    accepted, rejected = [], []
    for row in train:
        path = CANDIDATES / row["image_file"]
        class_id = int(row["class_id"])
        result = model.predict(str(path), conf=0.20, imgsz=640, verbose=False)[0]
        expected = [box for box in result.boxes if int(box.cls.item()) == class_id and float(box.conf.item()) >= 0.35]
        if not expected:
            rejected.append({"image_file": row["image_file"], "reason": "no_expected_box_above_0.35"})
            continue
        width, height = Image.open(path).size
        labels = []
        for box in expected:
            x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
            area = (x2 - x1) * (y2 - y1) / (width * height)
            if not 0.003 <= area <= 0.95:
                continue
            labels.append(f"{class_id} {(x1+x2)/(2*width):.6f} {(y1+y2)/(2*height):.6f} {(x2-x1)/width:.6f} {(y2-y1)/height:.6f}")
        if not labels:
            rejected.append({"image_file": row["image_file"], "reason": "box_area_filter"})
            continue
        name = f"inat_{row['photo_id']}.jpg"
        shutil.copy2(path, DEST / "train" / "images" / name)
        (DEST / "train" / "labels" / name.replace(".jpg", ".txt")).write_text("\n".join(labels) + "\n", encoding="utf-8")
        accepted.append({"image_file": row["image_file"], "training_name": name,
                         "class_id": class_id, "boxes": len(labels), "source_url": row["observation_url"],
                         "license": row["license"], "attribution": row["attribution"]})

    source_yaml = yaml.safe_load((SOURCE / "data.yaml").read_text(encoding="utf-8"))
    source_yaml["path"] = str(DEST)
    (DEST / "data.yaml").write_text(yaml.safe_dump(source_yaml, allow_unicode=True, sort_keys=False), encoding="utf-8")
    report = {
        "seed": SEED, "teacher": str(TEACHER), "pseudo_label_confidence_min": 0.35,
        "external_train_candidates": len(train), "external_pseudo_labeled": len(accepted),
        "external_holdout": len(holdout),
        "pseudo_by_class": dict(Counter(str(row["class_id"]) for row in accepted)),
        "holdout_by_class": dict(Counter(row["class_id"] for row in holdout)),
        "warning": "Las cajas son propuestas de YOLOv8 V2 sin revisión humana; la clase y el hospedero no han sido verificados en campo.",
        "accepted": accepted, "rejected": rejected,
        "holdout": [{"image_file": row["image_file"], "class_id": int(row["class_id"]),
                     "observation_id": row["observation_id"], "observation_url": row["observation_url"]} for row in holdout],
    }
    (DEST / "provenance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("external_train_candidates", "external_pseudo_labeled", "external_holdout", "pseudo_by_class", "holdout_by_class")}, indent=2))


if __name__ == "__main__":
    main()

"""Separa por foto original la exportación YOLOv8 de Roboflow del equipo."""

from __future__ import annotations

import collections
import json
import random
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "dataset_candidates" / "roboflow_companero_v1"
DEST = ROOT / "training_data" / "roboflow_v1_grouped"


def main() -> None:
    data = yaml.safe_load((SOURCE / "data.yaml").read_text(encoding="utf-8"))
    if len(data["names"]) != 7:
        raise ValueError("La exportación debe contener siete clases")
    images = sorted((SOURCE / "train" / "images").glob("*"))
    groups = collections.defaultdict(list)
    for image in images:
        if ".rf." not in image.name:
            raise ValueError(f"No se reconoce el nombre de variante: {image}")
        group = image.name.split(".rf.")[0]
        label = SOURCE / "train" / "labels" / f"{image.stem}.txt"
        if not label.is_file():
            raise ValueError(f"Falta etiqueta para {image}")
        classes = {int(line.split()[0]) for line in label.read_text().splitlines() if line.strip()}
        if len(classes) != 1:
            raise ValueError(f"Foto sin una clase clara: {image}")
        groups[group].append((image, label, next(iter(classes))))
    if len(groups) != 99 or any(len(items) != 3 for items in groups.values()):
        raise ValueError("Se esperaban 99 fotos originales con tres variantes cada una")

    by_class = collections.defaultdict(list)
    for group, items in groups.items():
        if len({item[2] for item in items}) != 1:
            raise ValueError(f"Las variantes discrepan en clase: {group}")
        by_class[items[0][2]].append(group)
    if set(by_class) != set(range(7)):
        raise ValueError(f"Faltan clases: {set(range(7)) - set(by_class)}")

    rng = random.Random(42)
    assignments = {}
    for class_id, keys in sorted(by_class.items()):
        rng.shuffle(keys)
        count = len(keys)
        n_test = max(1, round(count * 0.15))
        n_val = max(1, round(count * 0.15))
        if count - n_test - n_val < 1:
            raise ValueError(f"Muy pocos originales de clase {class_id}")
        for index, key in enumerate(keys):
            assignments[key] = "test" if index < n_test else "val" if index < n_test + n_val else "train"

    counts = collections.defaultdict(lambda: collections.Counter())
    for key, items in groups.items():
        split = assignments[key]
        for image, label, class_id in items:
            for source, kind in ((image, "images"), (label, "labels")):
                target = DEST / split / kind / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            counts[split][class_id] += 1
    config = {"path": str(DEST), "train": "train/images", "val": "val/images",
              "test": "test/images", "nc": 7, "names": data["names"]}
    (DEST / "data.yaml").write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    report = {"source_originals": len(groups), "source_augmented": len(images),
              "group_assignments": assignments,
              "images_per_split_class": {k: dict(v) for k, v in counts.items()},
              "limitation": "YOLOv8 V2 likely trained on these originals; this split is not an independent comparison with V2."}
    (DEST / "split_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["images_per_split_class"], indent=2))


if __name__ == "__main__":
    main()

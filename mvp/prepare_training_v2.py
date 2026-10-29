"""Usa más originales de Roboflow para entrenar, sin tocar la prueba externa."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT / "training_data" / "semisupervised_v1"
DEST = ROOT / "training_data" / "semisupervised_v2"


def main() -> None:
    if DEST.exists():
        raise RuntimeError(f"La salida ya existe; no se sobreescribirá: {DEST}")
    for split in ("train", "val"):
        for kind in ("images", "labels"):
            shutil.copytree(PREVIOUS / split / kind, DEST / split / kind)
    for kind in ("images", "labels"):
        for source in (PREVIOUS / "test" / kind).glob("*"):
            if source.is_file() and source.suffix.lower() != ".cache":
                target = DEST / "train" / kind / source.name
                if target.exists():
                    raise RuntimeError(f"Nombre repetido: {target}")
                shutil.copy2(source, target)
    data = yaml.safe_load((PREVIOUS / "data.yaml").read_text(encoding="utf-8"))
    data["path"] = str(DEST)
    data.pop("test", None)  # La única prueba final es externa y no tiene cajas verificadas.
    (DEST / "data.yaml").write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    provenance = json.loads((PREVIOUS / "provenance.json").read_text(encoding="utf-8"))
    provenance["additional_roboflow_augmented_train_images"] = 48
    provenance["warning"] += " El test agrupado previo pasó a entrenamiento y ya no se usa como prueba."
    (DEST / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    print("train:", len(list((DEST / "train" / "images").glob("*.jpg"))))
    print("val:", len(list((DEST / "val" / "images").glob("*.jpg"))))
    print("prueba externa reservada:", len(provenance["holdout"]))


if __name__ == "__main__":
    main()

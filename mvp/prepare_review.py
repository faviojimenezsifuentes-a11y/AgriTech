"""Genera propuestas de recuadros y láminas para revisión humana.

No convierte las predicciones del modelo previo en etiquetas verificadas.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dataset_candidates" / "inaturalist"
REVIEW = DATA / "review"
MODEL = ROOT / "models" / "esparragos_yolov8n_v2.pt"


def main() -> None:
    with (DATA / "manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    REVIEW.mkdir(exist_ok=True)
    (REVIEW / "proposed_labels").mkdir(exist_ok=True)
    model = YOLO(str(MODEL))
    counts = Counter()
    cards: dict[int, list[tuple[Image.Image, str]]] = {}
    decisions = []
    for row in rows:
        image_path = DATA / row["image_file"]
        result = model.predict(str(image_path), imgsz=640, conf=0.15, verbose=False)[0]
        lines = []
        proposals = []
        for box in result.boxes:
            cid = int(box.cls.item())
            xywh = [float(v) for v in box.xywhn[0].tolist()]
            conf = float(box.conf.item())
            lines.append(f"{cid} " + " ".join(f"{v:.6f}" for v in xywh))
            proposals.append({"class_id": cid, "confidence": round(conf, 4), "xywh_normalized": xywh})
            counts[cid] += 1
        stem = image_path.stem
        (REVIEW / "proposed_labels" / f"{stem}.txt").write_text(
            "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
        )
        decisions.append({"image_file": row["image_file"], "proposals": proposals,
                          "reviewed": False, "approved": False})
        preview = Image.fromarray(result.plot()).convert("RGB")
        preview.thumbnail((350, 260))
        cards.setdefault(int(row["class_id"]), []).append((preview.copy(), stem))

    (REVIEW / "proposals.json").write_text(
        json.dumps(decisions, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for cid, items in cards.items():
        columns = 3
        rows_per_sheet = 6
        for page, offset in enumerate(range(0, len(items), columns * rows_per_sheet), start=1):
            subset = items[offset:offset + columns * rows_per_sheet]
            sheet = Image.new("RGB", (1120, 1 + ((len(subset) + 2) // 3) * 310), "white")
            draw = ImageDraw.Draw(sheet)
            for idx, (preview, stem) in enumerate(subset):
                x = 15 + (idx % 3) * 370
                y = 10 + (idx // 3) * 310
                sheet.paste(preview, (x, y))
                draw.text((x, y + 265), stem, fill="black")
            sheet.save(REVIEW / f"sheet_class_{cid}_page_{page}.jpg", quality=88)
    summary = {"images": len(rows), "proposed_box_counts": dict(counts),
               "status": "all_proposals_unreviewed"}
    (REVIEW / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

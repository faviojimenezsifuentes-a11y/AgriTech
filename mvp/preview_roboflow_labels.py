"""Crea láminas de una variante por original con las cajas del compañero."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "dataset_candidates" / "roboflow_companero_v1" / "train"
OUT = ROOT / "dataset_candidates" / "roboflow_companero_v1" / "review"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    classes = defaultdict(list)
    seen = set()
    for image in sorted((SOURCE / "images").glob("*")):
        key = image.name.split(".rf.")[0]
        if key in seen:
            continue
        seen.add(key)
        label = SOURCE / "labels" / f"{image.stem}.txt"
        boxes = [line.split() for line in label.read_text().splitlines() if line.strip()]
        cid = int(boxes[0][0])
        with Image.open(image) as original:
            preview = original.convert("RGB")
        draw = ImageDraw.Draw(preview)
        width, height = preview.size
        for _, x, y, w, h in boxes:
            x, y, w, h = [float(v) for v in (x, y, w, h)]
            draw.rectangle(((x-w/2)*width, (y-h/2)*height, (x+w/2)*width, (y+h/2)*height),
                           outline="red", width=3)
        preview.thumbnail((300, 250))
        classes[cid].append((preview, key))

    for cid, items in classes.items():
        for page, start in enumerate(range(0, len(items), 16), 1):
            subset = items[start:start+16]
            sheet = Image.new("RGB", (1280, ((len(subset)+3)//4)*295), "white")
            draw = ImageDraw.Draw(sheet)
            for index, (preview, key) in enumerate(subset):
                x = (index % 4) * 320 + 10
                y = (index // 4) * 295 + 10
                sheet.paste(preview, (x, y))
                draw.text((x, y+255), key, fill="black")
            sheet.save(OUT / f"class_{cid}_page_{page}.jpg", quality=88)
    print({cid: len(items) for cid, items in classes.items()})


if __name__ == "__main__":
    main()

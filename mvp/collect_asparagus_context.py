"""Descarga fotos licenciadas de espárrago como contexto de evaluación, no como negativos confirmados."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "dataset_candidates" / "asparagus_context"
API = "https://api.inaturalist.org/v1/observations"


def main() -> None:
    if (DEST / "manifest.csv").exists():
        raise RuntimeError("La colección ya existe; conserva su manifiesto original.")
    images = DEST / "images"
    images.mkdir(parents=True, exist_ok=True)
    response = requests.get(API, params={"taxon_id": 60265, "quality_grade": "research",
                                         "photo_license": "cc0,cc-by", "photos": "true",
                                         "per_page": 80, "order_by": "votes"}, timeout=30)
    response.raise_for_status()
    rows = []
    for observation in response.json()["results"]:
        if len(rows) >= 24:
            break
        photos = observation.get("photos") or []
        if not photos:
            continue
        photo = photos[0]
        license_code = photo.get("license_code", "").lower()
        if license_code not in {"cc0", "cc-by"}:
            continue
        url = photo["url"].replace("/square.", "/large.")
        name = f"inat_asparagus_{photo['id']}.jpg"
        target = images / name
        try:
            result = requests.get(url, timeout=30)
            result.raise_for_status()
            image = Image.open(io.BytesIO(result.content)).convert("RGB")
            if min(image.size) < 300:
                continue
            image.save(target, "JPEG", quality=90)
        except (requests.RequestException, OSError):
            continue
        rows.append({"image_file": f"images/{name}", "observation_id": observation["id"],
                     "observation_url": f"https://www.inaturalist.org/observations/{observation['id']}",
                     "photo_url": url, "license": license_code.upper(),
                     "attribution": photo.get("attribution", ""), "taxon": observation["taxon"]["name"],
                     "status": "asparagus_context_unreviewed_not_negative_ground_truth"})
    with (DEST / "manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Fotografías de contexto descargadas: {len(rows)}")


if __name__ == "__main__":
    main()

"""Contrato de carga de imágenes de la historia SCRUM-10."""

import io
import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as project


class UploadTests(unittest.TestCase):
    def test_accepts_jpeg_and_normalizes_to_rgb(self):
        output = io.BytesIO()
        Image.new("L", (64, 48), color=120).save(output, "JPEG")
        image = project.read_image(output.getvalue())
        self.assertEqual((image.width, image.height, image.mode), (64, 48, "RGB"))

    def test_rejects_non_image_and_small_image(self):
        with self.assertRaises(ValueError):
            project.read_image(b"not an image")
        output = io.BytesIO()
        Image.new("RGB", (16, 16)).save(output, "PNG")
        with self.assertRaises(ValueError):
            project.read_image(output.getvalue())


if __name__ == "__main__":
    unittest.main()

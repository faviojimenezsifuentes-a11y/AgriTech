"""Respuesta sin hallazgos de la historia SCRUM-12."""

import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as project


class EmptyModel:
    def predict(self, *_args, **_kwargs):
        return [type("Result", (), {"boxes": [], "names": {}})()]


class EmptyDetectionTests(unittest.TestCase):
    def test_empty_result_has_no_false_counts_or_boxes(self):
        original = project.get_model
        try:
            project.get_model = lambda _key="baseline": EmptyModel()
            result = project.predict_image(Image.new("RGB", (120, 100)), 0.3)
        finally:
            project.get_model = original
        self.assertEqual(result["detections"], [])
        self.assertEqual(result["counts"], {})
        self.assertEqual((result["width"], result["height"]), (120, 100))


if __name__ == "__main__":
    unittest.main()

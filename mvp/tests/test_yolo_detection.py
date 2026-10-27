"""Contrato de las cajas YOLO de la historia SCRUM-11."""

import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as project


class Scalar:
    def __init__(self, value):
        self.value = value

    def item(self):
        return self.value


class Coordinates:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values


class DetectionModel:
    def predict(self, *_args, **_kwargs):
        box = type("Box", (), {
            "cls": Scalar(0), "conf": Scalar(0.875),
            "xyxy": [Coordinates([10, 20, 80, 90])],
        })()
        result = type("Result", (), {"boxes": [box], "names": {0: "Chloridea virescens adulto"}})()
        return [result]


class DetectionTests(unittest.TestCase):
    def test_returns_box_class_confidence_and_count(self):
        original = project.get_model
        try:
            project.get_model = lambda _key="baseline": DetectionModel()
            result = project.predict_image(Image.new("RGB", (120, 100)), 0.3)
        finally:
            project.get_model = original
        self.assertEqual(result["detections"][0]["xyxy"], [10.0, 20.0, 80.0, 90.0])
        self.assertEqual(result["detections"][0]["class_name"], "Chloridea virescens adulto")
        self.assertEqual(result["detections"][0]["confidence"], 0.875)
        self.assertEqual(result["counts"], {"Chloridea virescens adulto": 1})


if __name__ == "__main__":
    unittest.main()

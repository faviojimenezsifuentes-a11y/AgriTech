"""Correspondencia de clases YOLO y términos SIGIA de SCRUM-13."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as project


class MappingTests(unittest.TestCase):
    def test_every_yolo_class_has_a_search_term(self):
        self.assertEqual(set(project.CLASS_NAMES), set(project.MAPEO_PLAGAS))
        for term, is_common_name in project.MAPEO_PLAGAS.values():
            self.assertTrue(term.strip())
            self.assertIsInstance(is_common_name, bool)

    def test_common_name_is_explicit_for_prodiplosis(self):
        self.assertEqual(project.MAPEO_PLAGAS["prodiplosis longifila larva"], ("CARACHA", True))


if __name__ == "__main__":
    unittest.main()

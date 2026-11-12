import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.services.pipeline import TicketTriagePipeline


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = TicketTriagePipeline()

    def test_bundled_gearbox_ticket(self):
        result = self.pipeline.analyze("Gearbox vibration has increased with abnormal noise", "wind", "TEST1")
        self.assertEqual(result["classification"]["category"], "gearbox_vibration")
        self.assertIn(result["severity"]["severity"], {"medium", "high", "critical"})
        self.assertIn("Wind", result["routing"]["primary_team"])

    def test_safety_override(self):
        result = self.pipeline.analyze("Smoke and exposed live cable; personnel at risk", "solar")
        self.assertEqual(result["classification"]["category"], "safety_hazard")
        self.assertEqual(result["severity"]["severity"], "critical")
        self.assertEqual(result["routing"]["primary_team"], "Site Safety")

    def test_unknown_ticket_falls_back(self):
        result = self.pipeline.analyze("Unusual issue observed; details are not yet available", "unknown")
        self.assertEqual(result["classification"]["category"], "general_maintenance")
        self.assertEqual(result["routing"]["primary_team"], "Maintenance Triage Desk")

    def test_empty_description_rejected(self):
        with self.assertRaises(ValueError):
            self.pipeline.analyze("   ", "wind")


if __name__ == "__main__":
    unittest.main()

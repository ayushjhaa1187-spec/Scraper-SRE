import unittest
from datetime import datetime
from backend.app.models import ScraperRun, RunStatus, DriftType
from backend.app.analyzer import detect_drift

class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.base_time = datetime.now()

    def create_run(self, run_id, extracted_data=None):
        return ScraperRun(
            id=run_id,
            scraper_id="scraper_1",
            timestamp=self.base_time,
            status=RunStatus.SUCCESS,
            duration_ms=100.0,
            items_extracted=len(extracted_data) if extracted_data else 0,
            extracted_data_sample=extracted_data
        )

    def test_null_spike_alert_when_data_becomes_empty(self):
        # Previous run had data
        last_run = self.create_run("run_1", [{"price": 10}, {"price": 20}])
        # Current run has no data (empty list)
        current_run = self.create_run("run_2", [])

        alerts = detect_drift(current_run, last_run)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].type, DriftType.NULL_SPIKE)
        self.assertEqual(alerts[0].severity, "HIGH")
        self.assertEqual(alerts[0].scraper_id, "scraper_1")
        self.assertEqual(alerts[0].run_id, "run_2")

    def test_null_spike_alert_when_data_becomes_none(self):
        # Previous run had data
        last_run = self.create_run("run_1", [{"price": 10}, {"price": 20}])
        # Current run has None for data
        current_run = self.create_run("run_2", None)

        alerts = detect_drift(current_run, last_run)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].type, DriftType.NULL_SPIKE)

    def test_no_alert_when_data_remains(self):
        last_run = self.create_run("run_1", [{"price": 10}])
        current_run = self.create_run("run_2", [{"price": 15}])

        alerts = detect_drift(current_run, last_run)

        # Schema is the same, no null spike
        self.assertEqual(len(alerts), 0)

    def test_no_alert_when_previously_empty_too(self):
        last_run = self.create_run("run_1", [])
        current_run = self.create_run("run_2", [])

        alerts = detect_drift(current_run, last_run)

        self.assertEqual(len(alerts), 0)


    def test_no_alert_when_last_run_is_none(self):
        current_run = self.create_run("run_2", [])

        alerts = detect_drift(current_run, None)

        self.assertEqual(len(alerts), 0)

if __name__ == '__main__':
    unittest.main()

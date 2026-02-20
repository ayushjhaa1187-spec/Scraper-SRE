import time
import requests
import traceback
import json
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

class ScraperObserver:
    def __init__(self, scraper_id: str, api_url: str = "http://localhost:8000/api/v1"):
        self.scraper_id = scraper_id
        self.api_url = api_url.rstrip("/")
        self.current_run_data = {
            "scraper_id": scraper_id,
            "status": "SUCCESS",
            "duration_ms": 0,
            "items_extracted": 0,
            "error_message": None,
            "extracted_data_sample": [],
            "html_snapshot": None
        }

    def capture_snapshot(self, html: str):
        """Capture the HTML snapshot for debugging/repair."""
        self.current_run_data["html_snapshot"] = html

    def capture_data(self, data: List[Dict[str, Any]]):
        """Capture the extracted data sample."""
        self.current_run_data["extracted_data_sample"] = data
        self.current_run_data["items_extracted"] = len(data)

    def log_error(self, error: Exception):
        """Log an error explicitly."""
        self.current_run_data["status"] = "FAILURE"
        self.current_run_data["error_message"] = str(error)

    def submit_run(self):
        """Submit the run data to the backend."""
        try:
            url = f"{self.api_url}/ingest"
            # print(f"Submitting run to {url} with data: {json.dumps(self.current_run_data, default=str)}")
            response = requests.post(url, json=self.current_run_data)
            response.raise_for_status()
            # print(f"Run submitted successfully: {response.json()}")
        except Exception as e:
            print(f"Failed to submit run metrics: {e}")

    @contextmanager
    def monitor(self):
        """Context manager to wrap the scraping logic."""
        start_time = time.time()
        try:
            yield self
        except Exception as e:
            self.log_error(e)
            raise e
        finally:
            end_time = time.time()
            self.current_run_data["duration_ms"] = (end_time - start_time) * 1000
            self.submit_run()

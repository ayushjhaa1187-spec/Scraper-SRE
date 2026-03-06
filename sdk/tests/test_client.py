import sys
from unittest.mock import MagicMock

# Mock requests before importing ScraperObserver to avoid ModuleNotFoundError
mock_requests = MagicMock()
sys.modules["requests"] = mock_requests

import pytest
from unittest.mock import patch
from sdk.scraper_sre.client import ScraperObserver

@patch("sdk.scraper_sre.client.time.time")
def test_monitor_success(mock_time):
    # Setup
    mock_time.side_effect = [100.0, 105.0]  # Start, End
    mock_requests.post.return_value.status_code = 200
    mock_requests.post.return_value.json.return_value = {"status": "ok"}

    observer = ScraperObserver(scraper_id="test-scraper")

    # Execute
    with observer.monitor() as obs:
        assert obs == observer

    # Verify
    assert observer.current_run_data["status"] == "SUCCESS"
    assert observer.current_run_data["duration_ms"] == 5000.0
    assert observer.current_run_data["error_message"] is None
    mock_requests.post.assert_called_once()
    mock_requests.post.reset_mock()

@patch("sdk.scraper_sre.client.time.time")
def test_monitor_failure(mock_time):
    # Setup
    mock_time.side_effect = [200.0, 202.0]  # Start, End
    mock_requests.post.return_value.status_code = 200
    observer = ScraperObserver(scraper_id="test-scraper")

    # Execute & Verify Exception (monitor re-raises)
    with pytest.raises(ValueError, match="Test error"):
        with observer.monitor():
            raise ValueError("Test error")

    # Verify State
    assert observer.current_run_data["status"] == "FAILURE"
    assert "Test error" in observer.current_run_data["error_message"]
    assert observer.current_run_data["duration_ms"] == 2000.0
    mock_requests.post.assert_called_once()
    mock_requests.post.reset_mock()

def test_monitor_submit_called_even_on_failure():
    observer = ScraperObserver(scraper_id="test-scraper")

    try:
        with observer.monitor():
            raise Exception("Fail")
    except:
        pass

    mock_requests.post.assert_called_once()
    mock_requests.post.reset_mock()

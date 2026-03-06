import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock MongoDB before importing app modules
os.environ["MONGODB_URL"] = "mock://"

from backend.app.main import app
from backend.app.database import mock_storage
from backend.app.models import RunStatus

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup: Ensure mock mode and empty storage
    os.environ["MONGODB_URL"] = "mock://"
    mock_storage["scrapers"].clear()
    mock_storage["runs"].clear()
    mock_storage["alerts"].clear()
    yield
    # Teardown
    mock_storage["scrapers"].clear()
    mock_storage["runs"].clear()
    mock_storage["alerts"].clear()


@patch("backend.app.main.analyze_run")
def test_ingest_run_success(mock_analyze_run):
    payload = {
        "scraper_id": "test_scraper_123",
        "status": "SUCCESS",
        "duration_ms": 150.5,
        "items_extracted": 25,
        "html_snapshot": "<html><body>Test</body></html>",
        "extracted_data_sample": [{"title": "Test Item"}]
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "processing"

    # Verify background task was called
    mock_analyze_run.assert_called_once()

    # Verify database was updated
    assert len(mock_storage["runs"]) == 1
    saved_run = mock_storage["runs"][0]
    assert saved_run["scraper_id"] == "test_scraper_123"
    assert saved_run["status"] == "SUCCESS"
    assert saved_run["duration_ms"] == 150.5
    assert saved_run["items_extracted"] == 25
    assert saved_run["html_snapshot"] == "<html><body>Test</body></html>"
    assert saved_run["extracted_data_sample"] == [{"title": "Test Item"}]


@patch("backend.app.main.analyze_run")
def test_ingest_run_failure(mock_analyze_run):
    payload = {
        "scraper_id": "test_scraper_456",
        "status": "FAILURE",
        "duration_ms": 45.0,
        "items_extracted": 0,
        "error_message": "Connection timeout",
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "processing"

    # Verify background task was called
    mock_analyze_run.assert_called_once()

    # Verify database was updated
    assert len(mock_storage["runs"]) == 1
    saved_run = mock_storage["runs"][0]
    assert saved_run["scraper_id"] == "test_scraper_456"
    assert saved_run["status"] == "FAILURE"
    assert saved_run["duration_ms"] == 45.0
    assert saved_run["items_extracted"] == 0
    assert saved_run["error_message"] == "Connection timeout"
    assert saved_run["html_snapshot"] is None
    assert saved_run["extracted_data_sample"] is None


@patch("backend.app.main.analyze_run")
def test_ingest_run_missing_fields(mock_analyze_run):
    # Missing status, duration_ms, items_extracted
    payload = {
        "scraper_id": "test_scraper_789"
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 422
    assert len(mock_storage["runs"]) == 0
    # Validation error should prevent background task
    mock_analyze_run.assert_not_called()

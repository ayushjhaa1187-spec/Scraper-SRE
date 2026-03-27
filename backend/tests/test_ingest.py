import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

import os
os.environ["MONGODB_URL"] = "mock://"

from app.main import app
from app.database import mock_storage

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_mock_storage():
    mock_storage["scrapers"].clear()
    mock_storage["runs"].clear()
    mock_storage["alerts"].clear()
    yield


@patch("app.main.BackgroundTasks.add_task")
def test_ingest_successful_minimal(mock_add_task):
    payload = {
        "scraper_id": "test_scraper_123",
        "status": "SUCCESS",
        "duration_ms": 120.5,
        "items_extracted": 10
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "processing"

    # Check that it was saved to the db
    assert len(mock_storage["runs"]) == 1
    saved_run = mock_storage["runs"][0]
    assert saved_run["scraper_id"] == "test_scraper_123"
    assert saved_run["status"] == "SUCCESS"
    assert saved_run["duration_ms"] == 120.5
    assert saved_run["items_extracted"] == 10
    assert saved_run["error_message"] is None

    # Check that the background task was added
    mock_add_task.assert_called_once()
    args, kwargs = mock_add_task.call_args
    from app.main import analyze_run
    assert args[0] == analyze_run
    assert args[1].scraper_id == "test_scraper_123"

@patch("app.main.BackgroundTasks.add_task")
def test_ingest_successful_all_fields(mock_add_task):
    payload = {
        "scraper_id": "test_scraper_456",
        "status": "FAILURE",
        "duration_ms": 300.0,
        "items_extracted": 0,
        "error_message": "Timeout error",
        "extracted_data_sample": [{"title": "Test"}],
        "html_snapshot": "<html><body>Error</body></html>"
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 200

    assert len(mock_storage["runs"]) == 1
    saved_run = mock_storage["runs"][0]
    assert saved_run["scraper_id"] == "test_scraper_456"
    assert saved_run["status"] == "FAILURE"
    assert saved_run["error_message"] == "Timeout error"
    assert saved_run["extracted_data_sample"] == [{"title": "Test"}]
    assert saved_run["html_snapshot"] == "<html><body>Error</body></html>"

    mock_add_task.assert_called_once()

def test_ingest_invalid_data():
    # Missing required 'scraper_id'
    payload = {
        "status": "SUCCESS",
        "duration_ms": 120.5,
        "items_extracted": 10
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 422  # Unprocessable Entity (validation error)

    # Missing required 'status'
    payload = {
        "scraper_id": "test",
        "duration_ms": 120.5,
        "items_extracted": 10
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 422

    # Invalid 'status' value
    payload = {
        "scraper_id": "test",
        "status": "UNKNOWN_STATUS",
        "duration_ms": 120.5,
        "items_extracted": 10
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 422

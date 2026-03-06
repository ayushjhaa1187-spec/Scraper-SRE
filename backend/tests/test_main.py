import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import RunStatus, Scraper, ScraperConfig
from backend.app.database import mock_storage
import datetime
import uuid

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_mock_db():
    # Clear the mock database before each test
    mock_storage["scrapers"].clear()
    mock_storage["runs"].clear()
    mock_storage["alerts"].clear()
    yield

def test_ingest_run_success():
    scraper_id = str(uuid.uuid4())

    # Payload for a successful run
    payload = {
        "scraper_id": scraper_id,
        "status": RunStatus.SUCCESS.value,
        "duration_ms": 1500.5,
        "items_extracted": 42,
        "extracted_data_sample": [{"price": "$10", "title": "Product A"}]
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "processing"

    # Verify the run was saved in the mock database
    assert len(mock_storage["runs"]) == 1
    saved_run = mock_storage["runs"][0]
    assert saved_run["scraper_id"] == scraper_id
    assert saved_run["status"] == RunStatus.SUCCESS.value
    assert saved_run["items_extracted"] == 42
    assert saved_run["duration_ms"] == 1500.5

def test_ingest_run_failure():
    scraper_id = str(uuid.uuid4())

    # Payload for a failed run
    payload = {
        "scraper_id": scraper_id,
        "status": RunStatus.FAILURE.value,
        "duration_ms": 500.0,
        "items_extracted": 0,
        "error_message": "Timeout error",
        "html_snapshot": "<html>Timeout</html>"
    }

    response = client.post("/api/v1/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "processing"

    # Verify the run was saved in the mock database
    assert len(mock_storage["runs"]) == 1
    saved_run = mock_storage["runs"][0]
    assert saved_run["scraper_id"] == scraper_id
    assert saved_run["status"] == RunStatus.FAILURE.value
    assert saved_run["error_message"] == "Timeout error"

    # Verify the background task created an alert for the failure
    # Background tasks in FastAPI TestClient are executed inline
    assert len(mock_storage["alerts"]) == 1
    saved_alert = mock_storage["alerts"][0]
    assert saved_alert["scraper_id"] == scraper_id
    assert "Timeout error" in saved_alert["message"]

def test_ingest_run_missing_fields():
    # Missing 'duration_ms' and 'items_extracted'
    payload = {
        "scraper_id": str(uuid.uuid4()),
        "status": RunStatus.SUCCESS.value
    }

    response = client.post("/api/v1/ingest", json=payload)

    # Should fail validation
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

    # Extract the missing fields from the validation error
    missing_fields = [error["loc"][-1] for error in data["detail"]]
    assert "duration_ms" in missing_fields
    assert "items_extracted" in missing_fields

import pytest
from datetime import datetime
import sys
import unittest.mock

# Mock third-party dependencies that might be missing in test environment
unittest.mock.patch.dict('sys.modules', {
    'bs4': unittest.mock.MagicMock(),
    'lxml': unittest.mock.MagicMock(),
}).start()

from backend.app.analyzer import detect_drift
from backend.app.models import ScraperRun, RunStatus, DriftType

def create_mock_run(run_id: str, extracted_data: list = None) -> ScraperRun:
    return ScraperRun(
        id=run_id,
        scraper_id="scraper-1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=len(extracted_data) if extracted_data else 0,
        extracted_data_sample=extracted_data
    )

def test_detect_drift_no_schema_change():
    """Test that no alert is generated when schemas match."""
    last_run = create_mock_run("run-1", [{"title": "Item 1", "price": "10.00"}])
    current_run = create_mock_run("run-2", [{"title": "Item 2", "price": "20.00"}])

    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

def test_detect_drift_schema_change_missing_key():
    """Test that an alert is generated when a key is missing in the current run."""
    last_run = create_mock_run("run-1", [{"title": "Item 1", "price": "10.00"}])
    current_run = create_mock_run("run-2", [{"title": "Item 2"}])

    alerts = detect_drift(current_run, last_run)

    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert alerts[0].severity == "HIGH"
    assert "Missing keys: {'price'}" in alerts[0].message

def test_detect_drift_schema_change_added_key():
    """Test that an alert is generated when a key is added in the current run."""
    last_run = create_mock_run("run-1", [{"title": "Item 1"}])
    current_run = create_mock_run("run-2", [{"title": "Item 2", "price": "20.00"}])

    alerts = detect_drift(current_run, last_run)

    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert alerts[0].severity == "HIGH"
    assert "Added keys: {'price'}" in alerts[0].message

def test_detect_drift_schema_change_both_added_and_missing_keys():
    """Test that an alert is generated when a key is missing and another key is added."""
    last_run = create_mock_run("run-1", [{"title": "Item 1", "old_key": "val1"}])
    current_run = create_mock_run("run-2", [{"title": "Item 2", "new_key": "val2"}])

    alerts = detect_drift(current_run, last_run)

    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert alerts[0].severity == "HIGH"
    assert "Missing keys: {'old_key'}" in alerts[0].message
    assert "Added keys: {'new_key'}" in alerts[0].message

def test_detect_drift_no_last_run():
    """Test that no alert is generated when there is no last run."""
    current_run = create_mock_run("run-1", [{"title": "Item 1"}])

    alerts = detect_drift(current_run, None)
    assert len(alerts) == 0

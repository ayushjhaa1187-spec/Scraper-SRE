import pytest
from datetime import datetime
from app.models import ScraperRun, RunStatus, DriftType
from app.analyzer import detect_drift

def create_mock_run(id: str, sample_data=None):
    return ScraperRun(
        id=id,
        scraper_id="scraper_1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=len(sample_data) if sample_data else 0,
        extracted_data_sample=sample_data
    )

def test_detect_drift_no_last_run():
    current_run = create_mock_run("run_1", [{"price": "10"}])
    alerts = detect_drift(current_run, None)
    assert len(alerts) == 0

def test_detect_drift_null_spike():
    current_run = create_mock_run("run_2", [])
    last_run = create_mock_run("run_1", [{"price": "10"}])
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.NULL_SPIKE
    assert alerts[0].scraper_id == "scraper_1"
    assert alerts[0].run_id == "run_2"

def test_detect_drift_null_spike_none():
    current_run = create_mock_run("run_2", None)
    last_run = create_mock_run("run_1", [{"price": "10"}])
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.NULL_SPIKE

def test_detect_drift_schema_change_missing_keys():
    current_run = create_mock_run("run_2", [{"price": "10"}])
    last_run = create_mock_run("run_1", [{"price": "10", "title": "Product"}])
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert "Missing keys" in alerts[0].message
    assert "title" in alerts[0].message
    assert alerts[0].run_id == "run_2"

def test_detect_drift_schema_change_added_keys():
    current_run = create_mock_run("run_2", [{"price": "10", "title": "Product", "description": "Good"}])
    last_run = create_mock_run("run_1", [{"price": "10", "title": "Product"}])
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert "Added keys" in alerts[0].message
    assert "description" in alerts[0].message
    assert alerts[0].run_id == "run_2"

def test_detect_drift_schema_change_missing_and_added_keys():
    current_run = create_mock_run("run_2", [{"price": "10", "description": "Good"}])
    last_run = create_mock_run("run_1", [{"price": "10", "title": "Product"}])
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert "Missing keys" in alerts[0].message
    assert "title" in alerts[0].message
    assert "Added keys" in alerts[0].message
    assert "description" in alerts[0].message

def test_detect_drift_no_drift():
    current_run = create_mock_run("run_2", [{"price": "10", "title": "Product"}])
    last_run = create_mock_run("run_1", [{"price": "10", "title": "Product"}])
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

def test_detect_drift_both_empty():
    current_run = create_mock_run("run_2", [])
    last_run = create_mock_run("run_1", [])
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

def test_detect_drift_current_run_none_sample():
    current_run = create_mock_run("run_2", None)
    last_run = create_mock_run("run_1", None)
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

def test_detect_drift_last_run_none_sample():
    current_run = create_mock_run("run_2", [{"price": "10"}])
    last_run = create_mock_run("run_1", None)
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

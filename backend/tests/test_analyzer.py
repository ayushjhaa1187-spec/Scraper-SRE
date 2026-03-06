import pytest
from datetime import datetime
from app.models import ScraperRun, RunStatus, DriftType
from app.analyzer import detect_drift

def create_run(id="run1", sample_data=None):
    return ScraperRun(
        id=id,
        scraper_id="scraper1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=len(sample_data) if sample_data else 0,
        extracted_data_sample=sample_data
    )

def test_detect_drift_no_last_run():
    current_run = create_run(sample_data=[{"title": "Test"}])
    alerts = detect_drift(current_run, None)
    assert len(alerts) == 0

def test_detect_drift_null_spike():
    last_run = create_run(id="last", sample_data=[{"title": "Test"}])
    current_run = create_run(id="curr", sample_data=[])
    alerts = detect_drift(current_run, last_run)

    assert len(alerts) == 1
    assert alerts[0].type == DriftType.NULL_SPIKE
    assert alerts[0].severity == "HIGH"
    assert "0 items" in alerts[0].message

def test_detect_drift_no_data_both_runs():
    last_run = create_run(id="last", sample_data=[])
    current_run = create_run(id="curr", sample_data=[])
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

def test_detect_drift_schema_change_missing_keys():
    last_run = create_run(id="last", sample_data=[{"title": "A", "price": "10"}])
    current_run = create_run(id="curr", sample_data=[{"title": "B"}])
    alerts = detect_drift(current_run, last_run)

    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert alerts[0].severity == "HIGH"
    assert "price" in alerts[0].message

def test_detect_drift_schema_change_added_keys():
    last_run = create_run(id="last", sample_data=[{"title": "A"}])
    current_run = create_run(id="curr", sample_data=[{"title": "B", "price": "10"}])
    alerts = detect_drift(current_run, last_run)

    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert alerts[0].severity == "HIGH"
    assert "price" in alerts[0].message

def test_detect_drift_schema_change_mixed():
    last_run = create_run(id="last", sample_data=[{"title": "A", "old_field": "1"}])
    current_run = create_run(id="curr", sample_data=[{"title": "B", "new_field": "2"}])
    alerts = detect_drift(current_run, last_run)

    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert "old_field" in alerts[0].message
    assert "new_field" in alerts[0].message

def test_detect_drift_no_drift():
    last_run = create_run(id="last", sample_data=[{"title": "A", "price": "10"}])
    current_run = create_run(id="curr", sample_data=[{"title": "B", "price": "20"}])
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

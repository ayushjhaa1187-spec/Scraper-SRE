import pytest
from datetime import datetime
from backend.app.models import ScraperRun, RunStatus, DriftType
from backend.app.analyzer import detect_drift

def create_run(id_suffix: str, items: list) -> ScraperRun:
    return ScraperRun(
        id=f"run_{id_suffix}",
        scraper_id="scraper_1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=len(items) if items else 0,
        extracted_data_sample=items
    )

def test_detect_drift_no_last_run():
    current_run = create_run("curr", [{"title": "A"}])
    alerts = detect_drift(current_run, None)
    assert len(alerts) == 0

def test_detect_drift_null_spike():
    last_run = create_run("last", [{"title": "A"}])
    current_run = create_run("curr", [])

    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.NULL_SPIKE
    assert alerts[0].severity == "HIGH"
    assert alerts[0].scraper_id == "scraper_1"
    assert alerts[0].run_id == "run_curr"

def test_detect_drift_null_to_null():
    last_run = create_run("last", [])
    current_run = create_run("curr", [])

    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

def test_detect_drift_schema_change_missing_keys():
    last_run = create_run("last", [{"title": "A", "price": "$10"}])
    current_run = create_run("curr", [{"title": "B"}])

    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert alerts[0].severity == "HIGH"
    assert "Missing keys" in alerts[0].message
    assert "'price'" in alerts[0].message

def test_detect_drift_schema_change_added_keys():
    last_run = create_run("last", [{"title": "A"}])
    current_run = create_run("curr", [{"title": "B", "price": "$10"}])

    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert alerts[0].severity == "HIGH"
    assert "Added keys" in alerts[0].message
    assert "'price'" in alerts[0].message

def test_detect_drift_no_drift():
    last_run = create_run("last", [{"title": "A", "price": "$10"}])
    current_run = create_run("curr", [{"title": "B", "price": "$20"}])

    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

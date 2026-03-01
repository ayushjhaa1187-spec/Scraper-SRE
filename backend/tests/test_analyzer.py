import pytest
from datetime import datetime
from backend.app.models import ScraperRun, RunStatus, DriftType
from backend.app.analyzer import detect_drift

def test_detect_drift_no_last_run():
    current_run = ScraperRun(
        id="run_1",
        scraper_id="scraper_1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=5,
        extracted_data_sample=[{"price": "10", "title": "Item 1"}]
    )
    alerts = detect_drift(current_run, None)
    assert len(alerts) == 0

def test_detect_drift_null_spike():
    current_run = ScraperRun(
        id="run_2",
        scraper_id="scraper_1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=0,
        extracted_data_sample=[]
    )
    last_run = ScraperRun(
        id="run_1",
        scraper_id="scraper_1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=5,
        extracted_data_sample=[{"price": "10", "title": "Item 1"}]
    )
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.NULL_SPIKE

def test_detect_drift_schema_change():
    current_run = ScraperRun(
        id="run_2",
        scraper_id="scraper_1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=5,
        extracted_data_sample=[{"title": "Item 1"}]  # Missing "price"
    )
    last_run = ScraperRun(
        id="run_1",
        scraper_id="scraper_1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=5,
        extracted_data_sample=[{"price": "10", "title": "Item 1"}]
    )
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 1
    assert alerts[0].type == DriftType.SCHEMA_CHANGE
    assert "Missing keys: {'price'}" in alerts[0].message

def test_detect_drift_no_drift():
    current_run = ScraperRun(
        id="run_2",
        scraper_id="scraper_1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=5,
        extracted_data_sample=[{"price": "12", "title": "Item 2"}]
    )
    last_run = ScraperRun(
        id="run_1",
        scraper_id="scraper_1",
        timestamp=datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=5,
        extracted_data_sample=[{"price": "10", "title": "Item 1"}]
    )
    alerts = detect_drift(current_run, last_run)
    assert len(alerts) == 0

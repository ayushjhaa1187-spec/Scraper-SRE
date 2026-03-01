import pytest
from sdk.scraper_sre.client import ScraperObserver

def test_capture_data_success():
    observer = ScraperObserver(scraper_id="test-scraper")
    test_data = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"}
    ]

    observer.capture_data(test_data)

    assert observer.current_run_data["extracted_data_sample"] == test_data
    assert observer.current_run_data["items_extracted"] == 2

def test_capture_data_empty_list():
    observer = ScraperObserver(scraper_id="test-scraper")
    test_data = []

    observer.capture_data(test_data)

    assert observer.current_run_data["extracted_data_sample"] == []
    assert observer.current_run_data["items_extracted"] == 0

def test_capture_data_overrides_previous():
    observer = ScraperObserver(scraper_id="test-scraper")
    initial_data = [{"id": 1, "name": "Initial"}]
    new_data = [
        {"id": 2, "name": "New 1"},
        {"id": 3, "name": "New 2"},
        {"id": 4, "name": "New 3"}
    ]

    observer.capture_data(initial_data)
    assert observer.current_run_data["extracted_data_sample"] == initial_data
    assert observer.current_run_data["items_extracted"] == 1

    observer.capture_data(new_data)
    assert observer.current_run_data["extracted_data_sample"] == new_data
    assert observer.current_run_data["items_extracted"] == 3

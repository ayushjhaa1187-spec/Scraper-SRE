import pytest
import datetime
from app.models import Scraper, ScraperConfig, ScraperRun, Alert, RunStatus, DriftType
from app.main import trigger_repair
from app import database

# Fixture to setup mock DB
@pytest.fixture(autouse=True)
def setup_mock_db():
    database.MONGODB_URL = "mock://"
    database.mock_storage["scrapers"] = []
    database.mock_storage["runs"] = []
    database.mock_storage["alerts"] = []
    yield

@pytest.mark.asyncio
async def test_trigger_repair_schema_change_mock_llm(mocker):
    # Setup mock data
    config = ScraperConfig(name="test", target_url="http://test.com", selectors={"title": "h1", "price": ".price"})
    scraper = Scraper(id="scraper-1", config=config, created_at=datetime.datetime.now())
    await database.create_scraper(scraper)

    last_run = ScraperRun(
        id="run-old",
        scraper_id="scraper-1",
        timestamp=datetime.datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=1,
        extracted_data_sample=[{"title": "Test Product", "price": "$10"}],
        html_snapshot="<html><h1>Test Product</h1><div class='price'>$10</div></html>"
    )

    current_run = ScraperRun(
        id="run-new",
        scraper_id="scraper-1",
        timestamp=datetime.datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=1,
        extracted_data_sample=[{"title": "Test Product"}], # 'price' is missing
        html_snapshot="<html><h1>Test Product</h1><div class='new-price'>$10</div></html>"
    )

    alert = Alert(
        id="alert-1",
        scraper_id="scraper-1",
        run_id="run-new",
        type=DriftType.SCHEMA_CHANGE,
        message="Schema change detected",
        severity="HIGH",
        timestamp=datetime.datetime.now()
    )

    # Mock the LLM repair function so we can assert it was called correctly
    mock_repair = mocker.patch("app.main.mock_llm_repair", return_value="suggestion")
    mock_generate_prompt = mocker.patch("app.main.generate_fix_prompt", return_value="prompt")

    # Execute the function
    await trigger_repair(current_run, last_run, alert)

    # Verify the results
    assert mock_generate_prompt.call_count == 1
    mock_generate_prompt.assert_called_with(
        old_html=last_run.html_snapshot,
        new_html=current_run.html_snapshot,
        broken_selector=".price",
        field_name="price"
    )
    assert mock_repair.call_count == 1
    mock_repair.assert_called_with("prompt")

@pytest.mark.asyncio
async def test_trigger_repair_null_spike(mocker):
    # Setup mock data
    config = ScraperConfig(name="test", target_url="http://test.com", selectors={"title": "h1", "price": ".price"})
    scraper = Scraper(id="scraper-1", config=config, created_at=datetime.datetime.now())
    await database.create_scraper(scraper)

    last_run = ScraperRun(
        id="run-old",
        scraper_id="scraper-1",
        timestamp=datetime.datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=1,
        extracted_data_sample=[{"title": "Test Product", "price": "$10"}],
        html_snapshot="<html><h1>Test Product</h1><div class='price'>$10</div></html>"
    )

    current_run = ScraperRun(
        id="run-new",
        scraper_id="scraper-1",
        timestamp=datetime.datetime.now(),
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=1,
        extracted_data_sample=[{"title": None, "price": None}],
        html_snapshot="<html><div>Test Product</div><div class='new-price'>$10</div></html>"
    )

    alert = Alert(
        id="alert-1",
        scraper_id="scraper-1",
        run_id="run-new",
        type=DriftType.NULL_SPIKE,
        message="Null spike detected",
        severity="HIGH",
        timestamp=datetime.datetime.now()
    )

    # Mock the LLM repair function
    mock_repair = mocker.patch("app.main.mock_llm_repair", return_value="suggestion")
    mock_generate_prompt = mocker.patch("app.main.generate_fix_prompt", return_value="prompt")

    # Execute the function
    await trigger_repair(current_run, last_run, alert)

    # Verify the results
    assert mock_generate_prompt.call_count == 2
    # Check that it called it for both selectors
    mock_generate_prompt.assert_any_call(
        old_html=last_run.html_snapshot,
        new_html=current_run.html_snapshot,
        broken_selector="h1",
        field_name="title"
    )
    mock_generate_prompt.assert_any_call(
        old_html=last_run.html_snapshot,
        new_html=current_run.html_snapshot,
        broken_selector=".price",
        field_name="price"
    )
    assert mock_repair.call_count == 2

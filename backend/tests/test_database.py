import pytest
import os
from datetime import datetime, timedelta, timezone

os.environ["MONGODB_URL"] = "mock://"

from app.database import get_last_successful_run, save_run, mock_storage
from app.models import ScraperRun, RunStatus

@pytest.fixture(autouse=True)
def clean_storage():
    mock_storage["scrapers"] = []
    mock_storage["runs"] = []
    mock_storage["alerts"] = []
    yield
    mock_storage["scrapers"] = []
    mock_storage["runs"] = []
    mock_storage["alerts"] = []

@pytest.mark.asyncio
async def test_get_last_successful_run_empty():
    run = await get_last_successful_run("scraper1")
    assert run is None

@pytest.mark.asyncio
async def test_get_last_successful_run_filters_by_scraper():
    now = datetime.now(timezone.utc)

    run1 = ScraperRun(
        id="run1",
        scraper_id="scraper1",
        timestamp=now,
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=10
    )
    run2 = ScraperRun(
        id="run2",
        scraper_id="scraper2",
        timestamp=now,
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=10
    )

    await save_run(run1)
    await save_run(run2)

    last_run = await get_last_successful_run("scraper1")
    assert last_run is not None
    assert last_run.id == "run1"

@pytest.mark.asyncio
async def test_get_last_successful_run_filters_by_status():
    now = datetime.now(timezone.utc)

    run1 = ScraperRun(
        id="run1",
        scraper_id="scraper1",
        timestamp=now - timedelta(minutes=10),
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=10
    )
    run2 = ScraperRun(
        id="run2",
        scraper_id="scraper1",
        timestamp=now,
        status=RunStatus.FAILURE,
        duration_ms=100,
        items_extracted=0,
        error_message="failed"
    )

    await save_run(run1)
    await save_run(run2)

    last_run = await get_last_successful_run("scraper1")
    assert last_run is not None
    assert last_run.id == "run1"

@pytest.mark.asyncio
async def test_get_last_successful_run_sorts_by_timestamp():
    now = datetime.now(timezone.utc)

    run1 = ScraperRun(
        id="run1",
        scraper_id="scraper1",
        timestamp=now - timedelta(minutes=10),
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=10
    )
    run2 = ScraperRun(
        id="run2",
        scraper_id="scraper1",
        timestamp=now,
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=10
    )
    run3 = ScraperRun(
        id="run3",
        scraper_id="scraper1",
        timestamp=now - timedelta(minutes=5),
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=10
    )

    await save_run(run1)
    await save_run(run2)
    await save_run(run3)

    last_run = await get_last_successful_run("scraper1")
    assert last_run is not None
    assert last_run.id == "run2"

@pytest.mark.asyncio
async def test_get_last_successful_run_excludes_run_id():
    now = datetime.now(timezone.utc)

    run1 = ScraperRun(
        id="run1",
        scraper_id="scraper1",
        timestamp=now - timedelta(minutes=10),
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=10
    )
    run2 = ScraperRun(
        id="run2",
        scraper_id="scraper1",
        timestamp=now,
        status=RunStatus.SUCCESS,
        duration_ms=100,
        items_extracted=10
    )

    await save_run(run1)
    await save_run(run2)

    last_run = await get_last_successful_run("scraper1", exclude_run_id="run2")
    assert last_run is not None
    assert last_run.id == "run1"

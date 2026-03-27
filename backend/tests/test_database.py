import pytest
from datetime import datetime, timezone
import backend.app.database as db
from backend.app.models import Scraper, ScraperConfig, ScraperRun, Alert, RunStatus, DriftType

@pytest.fixture(autouse=True)
def setup_teardown():
    # Set MONGODB_URL to mock mode
    original_url = db.MONGODB_URL
    db.MONGODB_URL = "mock://"

    # Clear mock storage before each test
    db.mock_storage["scrapers"] = []
    db.mock_storage["runs"] = []
    db.mock_storage["alerts"] = []

    yield

    # Restore MONGODB_URL
    db.MONGODB_URL = original_url

def create_dummy_scraper(id="test-scraper-1"):
    return Scraper(
        id=id,
        config=ScraperConfig(
            name="Test Scraper",
            target_url="https://example.com",
            selectors={"title": "h1"}
        ),
        created_at=datetime.now(timezone.utc)
    )

def create_dummy_run(id="run-1", scraper_id="test-scraper-1", status=RunStatus.SUCCESS, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return ScraperRun(
        id=id,
        scraper_id=scraper_id,
        timestamp=timestamp,
        status=status,
        duration_ms=100.0,
        items_extracted=10,
    )

def create_dummy_alert(id="alert-1", scraper_id="test-scraper-1", run_id="run-1", timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return Alert(
        id=id,
        scraper_id=scraper_id,
        run_id=run_id,
        type=DriftType.SCHEMA_CHANGE,
        message="Missing title",
        severity="HIGH",
        timestamp=timestamp
    )

@pytest.mark.asyncio
async def test_create_and_get_scraper():
    scraper = create_dummy_scraper()

    # create_scraper
    await db.create_scraper(scraper)
    assert len(db.mock_storage["scrapers"]) == 1

    # get_scraper (exists)
    retrieved = await db.get_scraper(scraper.id)
    assert retrieved is not None
    assert retrieved.id == scraper.id

    # get_scraper (not exists)
    retrieved_none = await db.get_scraper("non-existent")
    assert retrieved_none is None

@pytest.mark.asyncio
async def test_get_all_scrapers():
    assert len(await db.get_all_scrapers()) == 0

    await db.create_scraper(create_dummy_scraper("scraper-1"))
    await db.create_scraper(create_dummy_scraper("scraper-2"))

    all_scrapers = await db.get_all_scrapers()
    assert len(all_scrapers) == 2
    ids = [s.id for s in all_scrapers]
    assert "scraper-1" in ids
    assert "scraper-2" in ids

@pytest.mark.asyncio
async def test_save_and_get_runs():
    scraper_id = "test-scraper-1"

    run1 = create_dummy_run("run-1", scraper_id, timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc))
    run2 = create_dummy_run("run-2", scraper_id, timestamp=datetime(2023, 1, 2, tzinfo=timezone.utc))

    await db.save_run(run1)
    await db.save_run(run2)

    assert len(db.mock_storage["runs"]) == 2

    # get_runs (should be ordered by timestamp desc)
    runs = await db.get_runs(scraper_id)
    assert len(runs) == 2
    assert runs[0].id == "run-2"
    assert runs[1].id == "run-1"

    # get_runs with limit
    runs_limited = await db.get_runs(scraper_id, limit=1)
    assert len(runs_limited) == 1
    assert runs_limited[0].id == "run-2"

@pytest.mark.asyncio
async def test_get_last_successful_run():
    scraper_id = "test-scraper-1"

    # Initial state
    assert await db.get_last_successful_run(scraper_id) is None

    run_fail = create_dummy_run("run-fail", scraper_id, RunStatus.FAILURE, datetime(2023, 1, 1, tzinfo=timezone.utc))
    run_success1 = create_dummy_run("run-success1", scraper_id, RunStatus.SUCCESS, datetime(2023, 1, 2, tzinfo=timezone.utc))
    run_success2 = create_dummy_run("run-success2", scraper_id, RunStatus.SUCCESS, datetime(2023, 1, 3, tzinfo=timezone.utc))

    await db.save_run(run_fail)
    await db.save_run(run_success1)
    await db.save_run(run_success2)

    # Should get the latest success
    last_success = await db.get_last_successful_run(scraper_id)
    assert last_success is not None
    assert last_success.id == "run-success2"

    # Should exclude a specific run
    excluded_success = await db.get_last_successful_run(scraper_id, exclude_run_id="run-success2")
    assert excluded_success is not None
    assert excluded_success.id == "run-success1"

    # Should return None if only failed runs are available after exclusion
    none_success = await db.get_last_successful_run("non-existent")
    assert none_success is None

@pytest.mark.asyncio
async def test_save_and_get_alerts():
    scraper_id = "test-scraper-1"

    alert1 = create_dummy_alert("alert-1", scraper_id, timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc))
    alert2 = create_dummy_alert("alert-2", scraper_id, timestamp=datetime(2023, 1, 2, tzinfo=timezone.utc))

    await db.save_alert(alert1)
    await db.save_alert(alert2)

    assert len(db.mock_storage["alerts"]) == 2

    # get_alerts (should be ordered by timestamp desc)
    alerts = await db.get_alerts(scraper_id)
    assert len(alerts) == 2
    assert alerts[0].id == "alert-2"
    assert alerts[1].id == "alert-1"

    # get_alerts with limit
    alerts_limited = await db.get_alerts(scraper_id, limit=1)
    assert len(alerts_limited) == 1
    assert alerts_limited[0].id == "alert-2"

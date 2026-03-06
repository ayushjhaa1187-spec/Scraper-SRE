import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from backend.app.models import ScraperRun, RunStatus
from backend.app import database

@pytest.fixture(autouse=True)
def setup_mock_db():
    # Ensure we're using mock DB for tests
    assert database.MONGODB_URL.startswith("mock://")
    # Clear mock storage before each test
    database.mock_storage["runs"].clear()
    yield
    # Clear after test as well
    database.mock_storage["runs"].clear()

@pytest.mark.asyncio
async def test_save_run_mock():
    # Create a mock ScraperRun
    run = ScraperRun(
        id="test_run_1",
        scraper_id="scraper_1",
        timestamp=datetime.now(timezone.utc),
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        items_extracted=10
    )

    # Save the run
    await database.save_run(run)

    # Verify it was saved to mock_storage
    assert len(database.mock_storage["runs"]) == 1
    saved_run = database.mock_storage["runs"][0]

    # Verify the contents
    assert saved_run["id"] == "test_run_1"
    assert saved_run["scraper_id"] == "scraper_1"
    assert saved_run["status"] == "SUCCESS"
    assert saved_run["duration_ms"] == 100.0
    assert saved_run["items_extracted"] == 10

@pytest.mark.asyncio
async def test_save_run_mongodb():
    # Create a mock ScraperRun
    run = ScraperRun(
        id="test_run_2",
        scraper_id="scraper_2",
        timestamp=datetime.now(timezone.utc),
        status=RunStatus.FAILURE,
        duration_ms=250.0,
        items_extracted=0,
        error_message="Connection timeout"
    )

    # We need to temporarily patch MONGODB_URL and db
    with patch("backend.app.database.MONGODB_URL", "mongodb://localhost:27017"):
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        mock_db.runs = mock_collection

        with patch("backend.app.database.db", mock_db):
            # Call save_run
            await database.save_run(run)

            # Verify insert_one was called with the correct data
            mock_collection.insert_one.assert_called_once()
            called_arg = mock_collection.insert_one.call_args[0][0]

            assert called_arg["id"] == "test_run_2"
            assert called_arg["scraper_id"] == "scraper_2"
            assert called_arg["status"] == "FAILURE"
            assert called_arg["duration_ms"] == 250.0
            assert called_arg["items_extracted"] == 0
            assert called_arg["error_message"] == "Connection timeout"

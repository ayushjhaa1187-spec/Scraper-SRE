import pytest
from unittest.mock import patch, MagicMock

# Import it globally before using it in patches
import app.database as database

@pytest.fixture(autouse=True)
def mock_env():
    # Setup: override MONGODB_URL
    with patch("app.database.MONGODB_URL", "mongodb://localhost:27017"):
        yield

@pytest.mark.asyncio
async def test_connect_to_mongo_success():
    mock_client_instance = MagicMock()
    mock_db = MagicMock()
    mock_client_instance.__getitem__.return_value = mock_db

    # Reset globals
    database.client = None
    database.db = None

    with patch("motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_client_instance) as mock_mongo:
        with patch("builtins.print") as mock_print:
            await database.connect_to_mongo()

            mock_mongo.assert_called_once_with("mongodb://localhost:27017")
            mock_print.assert_called_once_with("Connected to MongoDB at mongodb://localhost:27017")
            assert database.client == mock_client_instance
            assert database.db == mock_db

@pytest.mark.asyncio
async def test_connect_to_mongo_failure():
    # Reset globals
    database.client = None
    database.db = None

    with patch("motor.motor_asyncio.AsyncIOMotorClient", side_effect=Exception("Connection Timeout")) as mock_mongo:
        with patch("builtins.print") as mock_print:
            await database.connect_to_mongo()

            mock_mongo.assert_called_once_with("mongodb://localhost:27017")
            mock_print.assert_called_once_with("Failed to connect to MongoDB: Connection Timeout")
            assert database.client is None
            assert database.db is None

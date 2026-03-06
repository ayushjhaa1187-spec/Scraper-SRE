import pytest
from unittest.mock import patch, MagicMock
from backend.app import database

@pytest.fixture(autouse=True)
def setup_teardown():
    # Store original values
    original_url = database.MONGODB_URL
    original_client = getattr(database, 'client', None)
    original_db = getattr(database, 'db', None)

    yield

    # Restore original values
    database.MONGODB_URL = original_url
    database.client = original_client
    database.db = original_db

@pytest.mark.asyncio
async def test_connect_to_mongo_mock_db():
    database.MONGODB_URL = "mock://"
    database.client = None
    database.db = None

    with patch('builtins.print') as mock_print:
        await database.connect_to_mongo()

        mock_print.assert_called_with("Using In-Memory Mock Database")
        assert database.client is None
        assert database.db is None

@pytest.mark.asyncio
async def test_connect_to_mongo_success():
    database.MONGODB_URL = "mongodb://localhost:27017"
    database.client = None
    database.db = None

    mock_motor_client_instance = MagicMock()
    mock_motor_client_instance.__getitem__.return_value = MagicMock() # mock client[DB_NAME]

    with patch('motor.motor_asyncio.AsyncIOMotorClient', return_value=mock_motor_client_instance) as mock_motor_client:
        with patch('builtins.print') as mock_print:
            await database.connect_to_mongo()

            mock_motor_client.assert_called_with("mongodb://localhost:27017")
            assert database.client is mock_motor_client_instance
            assert database.db is mock_motor_client_instance.__getitem__.return_value
            mock_print.assert_called_with("Connected to MongoDB at mongodb://localhost:27017")

@pytest.mark.asyncio
async def test_connect_to_mongo_failure():
    database.MONGODB_URL = "mongodb://localhost:27017"
    database.client = None
    database.db = None

    test_exception = Exception("Connection failed")

    with patch('motor.motor_asyncio.AsyncIOMotorClient', side_effect=test_exception) as mock_motor_client:
        with patch('builtins.print') as mock_print:
            await database.connect_to_mongo()

            mock_motor_client.assert_called_with("mongodb://localhost:27017")
            assert database.client is None
            assert database.db is None
            mock_print.assert_called_with("Failed to connect to MongoDB: Connection failed")

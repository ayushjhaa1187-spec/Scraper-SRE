import pytest
from unittest.mock import MagicMock, patch
from app import database as db

@pytest.mark.asyncio
async def test_connect_to_mongo_success(capsys):
    """Test successful connection to MongoDB."""
    with patch("app.database.MONGODB_URL", "mongodb://localhost:27017"):
        mock_motor = MagicMock()
        mock_client = MagicMock()
        mock_motor.AsyncIOMotorClient.return_value = mock_client

        with patch.dict("sys.modules", {"motor.motor_asyncio": mock_motor}):
            await db.connect_to_mongo()

            captured = capsys.readouterr()
            assert "Connected to MongoDB at mongodb://localhost:27017" in captured.out

@pytest.mark.asyncio
async def test_connect_to_mongo_exception(capsys):
    """Test that connect_to_mongo gracefully handles connection exceptions."""
    with patch("app.database.MONGODB_URL", "mongodb://localhost:27017"):
        mock_motor = MagicMock()
        mock_motor.AsyncIOMotorClient.side_effect = Exception("Test Connection Error")

        with patch.dict("sys.modules", {"motor.motor_asyncio": mock_motor}):
            await db.connect_to_mongo()

            captured = capsys.readouterr()
            assert "Failed to connect to MongoDB: Test Connection Error" in captured.out

@pytest.mark.asyncio
async def test_connect_to_mongo_mock():
    """Test that connect_to_mongo uses mock storage when URL is mock://"""
    with patch("app.database.MONGODB_URL", "mock://"):
        # We verify that motor is not imported by making the mock raise if called
        mock_motor = MagicMock()
        mock_motor.AsyncIOMotorClient.side_effect = Exception("Should not import motor when using mock db")

        with patch.dict("sys.modules", {"motor.motor_asyncio": mock_motor}):
            await db.connect_to_mongo()
            # Should pass without exceptions and print mock message

import unittest
from unittest.mock import patch, MagicMock

class TestDatabase(unittest.IsolatedAsyncioTestCase):
    async def test_connect_to_mongo_mock(self):
        import app.database
        with patch("app.database.MONGODB_URL", "mock://test"):
            with patch("builtins.print") as mock_print:
                from app.database import connect_to_mongo
                await connect_to_mongo()
                mock_print.assert_called_with("Using In-Memory Mock Database")

    async def test_connect_to_mongo_success(self):
        import app.database
        with patch("app.database.MONGODB_URL", "mongodb://valid:27017"):
            with patch("builtins.print") as mock_print:
                from app.database import connect_to_mongo

                # Mock a successful client creation
                mock_client_instance = MagicMock()
                mock_db = MagicMock()
                mock_client_instance.__getitem__.return_value = mock_db
                mock_motor_client = MagicMock(return_value=mock_client_instance)

                with patch.dict("sys.modules", {"motor.motor_asyncio": type("MockModule", (), {"AsyncIOMotorClient": mock_motor_client})}):
                    await connect_to_mongo()

                # It should print connected message
                mock_print.assert_called_with("Connected to MongoDB at mongodb://valid:27017")

                # Verify that global client and db were set
                self.assertEqual(app.database.client, mock_client_instance)
                self.assertEqual(app.database.db, mock_db)

    async def test_connect_to_mongo_failure(self):
        import app.database
        with patch("app.database.MONGODB_URL", "mongodb://invalid:27017"):
            with patch("builtins.print") as mock_print:
                from app.database import connect_to_mongo

                # We want the AsyncIOMotorClient constructor to raise an exception
                mock_motor_client = MagicMock(side_effect=Exception("Connection timed out"))

                # Mock the module that gets imported inside connect_to_mongo
                with patch.dict("sys.modules", {"motor.motor_asyncio": type("MockModule", (), {"AsyncIOMotorClient": mock_motor_client})}):
                    await connect_to_mongo()

                # It should print "Failed to connect to MongoDB: Connection timed out"
                mock_print.assert_called_with("Failed to connect to MongoDB: Connection timed out")

if __name__ == "__main__":
    unittest.main()

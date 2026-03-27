import os
import sys
import unittest
from unittest.mock import patch

# Mock some sys.modules to prevent import errors in restricted environments if needed
# We are just testing the CORS initialization, but FastAPI will try to import everything.

class TestCorsConfiguration(unittest.TestCase):

    def setUp(self):
        # We need to reload the module to test the module-level execution
        if 'app.main' in sys.modules:
            del sys.modules['app.main']
        if 'backend.app.main' in sys.modules:
            del sys.modules['backend.app.main']

    @patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True)
    def test_cors_development(self):
        from backend.app.main import app

        # Find the CORSMiddleware
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == 'CORSMiddleware':
                cors_middleware = middleware
                break

        self.assertIsNotNone(cors_middleware)
        self.assertEqual(cors_middleware.kwargs.get("allow_origins"), ["*"])

    @patch.dict(os.environ, {"ENVIRONMENT": "production", "CORS_ORIGINS": "https://example.com, https://test.com "}, clear=True)
    def test_cors_production_with_origins(self):
        # Reloading module is required since CORS is configured at module level
        import importlib
        import backend.app.main
        importlib.reload(backend.app.main)
        from backend.app.main import app

        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == 'CORSMiddleware':
                cors_middleware = middleware
                break

        self.assertIsNotNone(cors_middleware)
        self.assertEqual(cors_middleware.kwargs.get("allow_origins"), ["https://example.com", "https://test.com"])

    @patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True)
    def test_cors_production_without_origins(self):
        import importlib
        import backend.app.main
        importlib.reload(backend.app.main)
        from backend.app.main import app

        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == 'CORSMiddleware':
                cors_middleware = middleware
                break

        self.assertIsNotNone(cors_middleware)
        self.assertEqual(cors_middleware.kwargs.get("allow_origins"), [])

if __name__ == '__main__':
    unittest.main()

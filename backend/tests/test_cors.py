import pytest
from fastapi.testclient import TestClient
import os
import sys
import unittest.mock

# Mock the database connection early before importing main
unittest.mock.patch.dict('os.environ', {'MONGODB_URL': 'mock://'}).start()
unittest.mock.patch.dict('sys.modules', {'bs4': unittest.mock.MagicMock(), 'lxml': unittest.mock.MagicMock()}).start()

from backend.app.main import app

client = TestClient(app)

def test_cors_allowed_origin():
    # Make a preflight request from an allowed origin
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Requested-With",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_disallowed_origin():
    # Make a preflight request from a disallowed origin
    headers = {
        "Origin": "http://evil.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Requested-With",
    }
    response = client.options("/", headers=headers)
    # The origin shouldn't be reflected in the allow-origin header for a disallowed origin
    assert response.headers.get("access-control-allow-origin") is None

def test_cors_custom_allowed_origins():
    # Test that we can override the environment variable
    with unittest.mock.patch.dict('os.environ', {'ALLOWED_ORIGINS': 'https://my-frontend.com'}):
        # We need to reload the app to pick up the new environment variable
        import importlib
        import backend.app.main
        importlib.reload(backend.app.main)
        custom_client = TestClient(backend.app.main.app)

        headers = {
            "Origin": "https://my-frontend.com",
            "Access-Control-Request-Method": "GET",
        }
        response = custom_client.options("/", headers=headers)
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://my-frontend.com"

        # Original default should now fail
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
        response = custom_client.options("/", headers=headers)
        assert response.headers.get("access-control-allow-origin") is None

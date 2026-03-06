import pytest
import os
import sys

# Mock sys.modules for any missing dependencies (if needed, though fastapi/motor are installed)
# We will just set MONGODB_URL before importing the app
os.environ["MONGODB_URL"] = "mock://"

from fastapi.testclient import TestClient
from app.main import app

# Ensure clean state for mock database
from app.database import mock_storage

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    mock_storage["scrapers"].clear()
    mock_storage["runs"].clear()
    mock_storage["alerts"].clear()

def test_register_scraper_valid():
    response = client.post(
        "/api/v1/register",
        json={
            "name": "Test Scraper",
            "target_url": "https://example.com/products",
            "selectors": {"title": "h1"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["config"]["name"] == "Test Scraper"
    # Pydantic HttpUrl to str adds trailing slash for domains without paths sometimes, but not if there is a path.
    # It parses "https://example.com/products" to "https://example.com/products" in v2
    assert data["config"]["target_url"] == "https://example.com/products"

def test_register_scraper_invalid_url():
    response = client.post(
        "/api/v1/register",
        json={
            "name": "Test Scraper",
            "target_url": "not-a-valid-url",
            "selectors": {"title": "h1"}
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "target_url" in str(data)

def test_register_scraper_name_too_long():
    response = client.post(
        "/api/v1/register",
        json={
            "name": "A" * 256,
            "target_url": "https://example.com/products",
            "selectors": {"title": "h1"}
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "name" in str(data)

def test_register_scraper_name_empty():
    response = client.post(
        "/api/v1/register",
        json={
            "name": "",
            "target_url": "https://example.com/products",
            "selectors": {"title": "h1"}
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "name" in str(data)

def test_register_scraper_selectors_too_large():
    selectors = {f"key_{i}": f"value_{i}" for i in range(101)}
    response = client.post(
        "/api/v1/register",
        json={
            "name": "Test Scraper",
            "target_url": "https://example.com/products",
            "selectors": selectors
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "selectors" in str(data)

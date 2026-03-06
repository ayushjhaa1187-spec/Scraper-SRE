import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Scraper SRE Platform API is running"}

def test_unauthenticated_access():
    response = client.get("/api/v1/scrapers")
    assert response.status_code == 403

def test_authenticated_access():
    response = client.get("/api/v1/scrapers", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200

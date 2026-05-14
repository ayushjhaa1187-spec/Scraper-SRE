import pytest
from fastapi.testclient import TestClient
from app.main import app, API_KEY

client = TestClient(app)

def test_unauthenticated_access_rejected():
    # Should fail without API key
    response = client.get("/api/v1/scrapers")
    assert response.status_code == 401
    # assert response.json() == {"detail": "Not authenticated"}

def test_invalid_api_key_rejected():
    # Should fail with wrong API key
    response = client.get("/api/v1/scrapers", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    # assert response.json() == {"detail": "Invalid API Key"}

def test_authenticated_access_allowed():
    # Should pass with correct API key
    response = client.get("/api/v1/scrapers", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_root_unauthenticated_allowed():
    # Root endpoint should not require auth
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Scraper SRE Platform API is running"}

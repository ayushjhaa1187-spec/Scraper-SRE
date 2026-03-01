import pytest
from pydantic import ValidationError
from backend.app.main import RegisterRequest

def test_register_request_valid_url():
    # Should not raise any validation error
    request = RegisterRequest(
        name="test_scraper",
        target_url="http://example.com/products",
        selectors={"title": "h1"}
    )
    assert request.name == "test_scraper"
    assert str(request.target_url) == "http://example.com/products"

def test_register_request_invalid_url():
    # Should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        RegisterRequest(
            name="test_scraper",
            target_url="not_a_valid_url",
            selectors={"title": "h1"}
        )
    assert "target_url" in str(exc_info.value)

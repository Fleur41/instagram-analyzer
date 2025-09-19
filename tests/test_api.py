import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Instagram Interaction Analyzer API"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_analyze_endpoint():
    # Test with invalid users (should fail gracefully)
    response = client.get("/analyze/nonexistentuser1/nonexistentuser2")
    assert response.status_code == 400

def test_analyze_post():
    # Test POST endpoint
    payload = {
        "user1": "test_user1",
        "user2": "test_user2",
        "use_credentials": False,
        "max_posts": 10,
        "max_stories": 5
    }
    
    response = client.post("/analyze", json=payload)
    assert response.status_code == 400  # Should fail with invalid users
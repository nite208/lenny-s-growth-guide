import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health/")
    assert r.status_code == 200

def test_chat_returns_session():
    r = client.post("/api/chat/", json={"message":"What is product-market fit?","mode":"chat"})
    assert r.status_code == 200
    assert "session_id" in r.json()

def test_essay_returns_artifact():
    r = client.post("/api/chat/", json={"message":"How do you build a growth loop?","mode":"essay"})
    data = r.json()
    assert data.get("artifact") is not None

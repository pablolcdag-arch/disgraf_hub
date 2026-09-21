import pytest
from fastapi.testclient import TestClient
from main import app
import os
import json

client = TestClient(app)

@pytest.fixture
def logged_in_client():
    from dependencies import USERS, sessions
    import secrets
    
    original_users = USERS.copy()
    USERS["test_seller"] = {"password": "pwd", "role": "seller"}
    
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = {"username": "test_seller", "role": "seller"}
    
    client.cookies.set("session_token", session_token)
    yield client
    
    client.cookies.delete("session_token")
    if session_token in sessions:
        del sessions[session_token]
    USERS.clear()
    USERS.update(original_users)

@pytest.fixture
def admin_client():
    from dependencies import USERS, sessions
    import secrets
    
    original_users = USERS.copy()
    USERS["test_admin"] = {"password": "pwd", "role": "admin"}
    
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = {"username": "test_admin", "role": "admin"}
    
    client.cookies.set("session_token", session_token)
    yield client
    
    client.cookies.delete("session_token")
    if session_token in sessions:
        del sessions[session_token]
    USERS.clear()
    USERS.update(original_users)

def test_log_quote(logged_in_client, monkeypatch):
    # Mock Telegram to avoid sending real messages during tests
    class MockResponse:
        status_code = 200
        text = "ok"
        
    def mock_post(*args, **kwargs):
        return MockResponse()
        
    import requests
    monkeypatch.setattr(requests, "post", mock_post)

    payload = {
        "client_name": "Test Client",
        "total": 1000,
        "products": [
            {"name": "Product 1", "unit": "Mts", "quantity": 10, "subtotal": 1000, "price": 100}
        ],
        "tipoB": True
    }
    
    response = logged_in_client.post("/api/log-quote", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_history_quotes(admin_client):
    response = admin_client.get("/api/history-quotes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_generate_quote_pdf(logged_in_client):
    payload = {
        "client_name": "Test Client",
        "total": 1000,
        "products": [
            {"name": "Product 1", "unit": "Mts", "quantity": 10, "subtotal": 1000, "price": 100}
        ],
        "tipoB": True,
        "globalDiscount": 0
    }
    
    response = logged_in_client.post("/api/generate-quote-pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


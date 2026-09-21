import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_page_get():
    response = client.get("/")
    assert response.status_code == 200
    assert "Disgraf Hub - Login" in response.text or "<form" in response.text

def test_login_success_admin(monkeypatch):
    # Setup mock users
    from dependencies import USERS
    original_users = USERS.copy()
    USERS["test_admin"] = {"password": "admin_password", "role": "admin"}
    
    response = client.post("/login", data={"username": "test_admin", "password": "admin_password"}, follow_redirects=False)
    
    # Must redirect to dashboard
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"
    assert "session_token" in response.cookies
    
    # Restore
    USERS.clear()
    USERS.update(original_users)

def test_login_success_seller(monkeypatch):
    from dependencies import USERS
    original_users = USERS.copy()
    USERS["test_seller"] = {"password": "seller_password", "role": "seller"}
    
    response = client.post("/login", data={"username": "test_seller", "password": "seller_password"}, follow_redirects=False)
    
    # Must redirect to cotizador
    assert response.status_code == 302
    assert response.headers["location"] == "/cotizador"
    assert "session_token" in response.cookies
    
    # Restore
    USERS.clear()
    USERS.update(original_users)

def test_login_failure():
    response = client.post("/login", data={"username": "wrong", "password": "wrong"}, follow_redirects=False)
    assert response.status_code == 200
    assert "Credenciales inv" in response.text

def test_logout():
    # Login first
    from dependencies import USERS
    original_users = USERS.copy()
    USERS["test_admin"] = {"password": "admin_password", "role": "admin"}
    
    client.post("/login", data={"username": "test_admin", "password": "admin_password"})
    
    # Logout
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    
    # Restore
    USERS.clear()
    USERS.update(original_users)


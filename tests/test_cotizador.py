import pytest
from fastapi.testclient import TestClient
from main import app
import os
import json

client = TestClient(app)

@pytest.fixture
def logged_in_client():
    from dependencies import USERS, JWT_SECRET_KEY, JWT_ALGORITHM
    import jwt
    from datetime import datetime, timedelta, timezone
    
    original_users = USERS.copy()
    USERS["test_seller"] = {"password": "pwd", "role": "seller"}
    
    payload = {
        "username": "test_seller",
        "role": "seller",
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    session_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    client.cookies.set("session_token", session_token)
    yield client
    
    client.cookies.delete("session_token")
    USERS.clear()
    USERS.update(original_users)

@pytest.fixture
def admin_client():
    from dependencies import USERS, JWT_SECRET_KEY, JWT_ALGORITHM
    import jwt
    from datetime import datetime, timedelta, timezone
    
    original_users = USERS.copy()
    USERS["test_admin"] = {"password": "pwd", "role": "admin"}
    
    payload = {
        "username": "test_admin",
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    session_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    client.cookies.set("session_token", session_token)
    yield client
    
    client.cookies.delete("session_token")
    USERS.clear()
    USERS.update(original_users)

@pytest.fixture
def mock_db(tmp_path, monkeypatch):
    import routes.cotizador_api
    monkeypatch.setattr(routes.cotizador_api, "DATA_DIR", str(tmp_path))
    import routes.ventas_api
    monkeypatch.setattr(routes.ventas_api, "DATA_DIR", str(tmp_path))
    
    import sqlite3
    db_path = tmp_path / "disgraf_hub.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comprobantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id TEXT,
            tipo_comprobante TEXT,
            numero_comprobante TEXT,
            fecha_emision TEXT,
            es_fiscal INTEGER,
            impacta_cc INTEGER,
            impacta_stock INTEGER,
            subtotal REAL,
            total_iva REAL,
            total REAL,
            estado TEXT,
            comprobante_asociado_id INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comprobantes_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comprobante_id INTEGER,
            producto_id TEXT,
            descripcion TEXT,
            cantidad REAL,
            precio_unitario REAL,
            alicuota_iva REAL,
            subtotal REAL,
            FOREIGN KEY(comprobante_id) REFERENCES comprobantes(id)
        )
    ''')
    conn.commit()
    conn.close()
    return tmp_path

def test_log_quote(logged_in_client, mock_db, monkeypatch):
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
            {"id": "1", "name": "Product 1", "unit": "Mts", "quantity": 10, "subtotal": 1000, "price": 100}
        ],
        "tipoB": True
    }
    
    response = logged_in_client.post("/api/cotizador/guardar", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_history_quotes(admin_client, mock_db):
    response = admin_client.get("/api/cotizador/historial")
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


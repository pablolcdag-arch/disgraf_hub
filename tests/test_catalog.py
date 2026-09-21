import pytest
from fastapi.testclient import TestClient
from main import app
import os
import json

client = TestClient(app)

@pytest.fixture
def mock_data_dir(tmp_path, monkeypatch):
    import routes.catalog_api
    monkeypatch.setattr(routes.catalog_api, "DATA_DIR", str(tmp_path))
    
    # Create maestro_productos.csv
    maestro = tmp_path / "maestro_productos.csv"
    maestro.write_text("Nº de producto;Nombre;Rubro;Precio ($);Unidad\n100;Vinilo;Carteleria;1000;Mts\n", encoding="utf-8")
    
    # Create productos_seleccionados.csv
    seleccionados = tmp_path / "productos_seleccionados.csv"
    seleccionados.write_text("codigo_producto,unidad\nVinilos,\n100,\n", encoding="utf-8")
    
    # Create categorias_meta.json
    meta = tmp_path / "categorias_meta.json"
    meta.write_text(json.dumps({"Vinilos": {"seo_text": "Texto SEO"}}), encoding="utf-8")
    
    return tmp_path

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

def test_load_catalog(admin_client, mock_data_dir):
    response = admin_client.get("/api/load-catalog")
    assert response.status_code == 200
    
    data = response.json()
    assert "saas_products" in data
    assert "selected_catalog" in data
    assert "category_meta" in data
    
    # Check maestro parsed
    assert len(data["saas_products"]) == 1
    assert data["saas_products"][0]["id"] == "100"
    
    # Check selected parsed
    assert len(data["selected_catalog"]) == 1
    assert data["selected_catalog"][0]["id"] == "100"
    assert data["selected_catalog"][0]["catalog_category"] == "Vinilos"
    
    # Check meta parsed
    assert "Vinilos" in data["category_meta"]
    assert data["category_meta"]["Vinilos"]["seo_text"] == "Texto SEO"


import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_app_startup():
    # Solo comprobar que app tiene rutas registradas (routers cargados exitosamente)
    assert len(app.routes) > 0

def test_ui_endpoints_redirect_without_auth():
    # Comprobar que endpoints protegidos devuelven redirección
    endpoints_to_root = ["/dashboard", "/cotizador", "/marketing", "/media", "/clientes"]
    for endpoint in endpoints_to_root:
        response = client.get(endpoint, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/"

    response_precios = client.get("/precios", follow_redirects=False)
    assert response_precios.status_code == 302
    assert response_precios.headers["location"] == "/dashboard"

def test_storefront_v2_home():
    # Endpoints públicos de v2 (tienda pública)
    response = client.get("/v2")
    assert response.status_code == 200
    # Verificamos que cargó la plantilla (básico)
    assert "html" in response.text.lower()

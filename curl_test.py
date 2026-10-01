import requests

url = "http://127.0.0.1:8000/api/ventas/comprobantes"
payload = {
    "cliente_id": "1748",
    "tipo_comprobante": "Nota de Crédito A",
    "subtotal": 103332.14,
    "total_iva": 21699.75,
    "total": 125031.89,
    "items": [
        {
            "producto_id": "1",
            "descripcion": "Posicionador",
            "cantidad": 1,
            "precio_unitario": 93817.60,
            "alicuota_iva": 21.0,
            "subtotal": 93817.60
        }
    ],
    "facturar_afip": True,
    "comprobante_asociado_id": "82"
}
# We don't have a session, so we might get 401 Unauthorized.
# But we patched main.py to print the Validation error if it fails BEFORE auth?
# Actually, dependencies.py `get_current_user` runs FIRST in the route.
# So we WILL get 401.

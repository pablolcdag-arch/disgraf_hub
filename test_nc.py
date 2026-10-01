import requests
import json

payload = {
    "cliente_id": "1",
    "tipo_comprobante": "Nota de Crédito A",
    "subtotal": 100,
    "total_iva": 21,
    "total": 121,
    "items": [],
    "facturar_afip": True,
    "comprobante_asociado_id": 81
}

# Just test pydantic parsing
from routes.ventas_api import ComprobanteCreate
try:
    c = ComprobanteCreate(**payload)
    print("Parsed comprobante_asociado_id:", c.comprobante_asociado_id)
except Exception as e:
    print("Error parsing:", e)


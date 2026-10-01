import requests

url = "https://hub.disgraf.com.ar/api/ventas/comprobantes"
# We'll get 401 Unauthorized, but let's see if we get 422!
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
response = requests.post(url, json=payload)
print(response.status_code)
print(response.text)

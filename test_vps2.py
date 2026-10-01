import requests

url_login = "https://hub.disgraf.com.ar/api/login"
resp_login = requests.post(url_login, data={"username": "admin", "password": "disgraf2024"})
token = resp_login.json().get("access_token")

url = "https://hub.disgraf.com.ar/api/ventas/comprobantes"
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

resp = requests.post(url, json=payload, cookies={"session_token": token})
print(resp.status_code)
print(resp.text)

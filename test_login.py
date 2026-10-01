import requests

session = requests.Session()
resp = session.post('http://127.0.0.1:8000/login', data={'username':'pablo', 'password':'admin1'}, allow_redirects=False)
print('LOGIN:', resp.status_code)
print('COOKIES:', session.cookies.get_dict())

token = session.cookies.get_dict().get('session_token')

payload = {
    'cliente_id': '1748',
    'tipo_comprobante': 'Nota de Crédito A',
    'subtotal': 103332.14,
    'total_iva': 21699.75,
    'total': 125031.89,
    'items': [
        {
            'producto_id': '1',
            'descripcion': 'Posicionador',
            'cantidad': 1,
            'precio_unitario': 93817.60,
            'alicuota_iva': 21.0,
            'subtotal': 93817.60
        }
    ],
    'facturar_afip': True,
    'comprobante_asociado_id': '82'
}
resp2 = session.post('http://127.0.0.1:8000/api/ventas/comprobantes', json=payload, cookies={'session_token': token})
print('VENTAS:', resp2.status_code)
print(resp2.text)

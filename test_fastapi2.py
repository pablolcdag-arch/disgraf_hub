import requests

session = requests.Session()
resp = session.post('http://127.0.0.1:8000/login', data={'username':'admin', 'password':'disgraf2024'})
print('LOGIN URL:', resp.url)
print('LOGIN STATUS:', resp.status_code)
print('COOKIES:', session.cookies.get_dict())

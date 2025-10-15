import requests

try:
    r = requests.get('http://127.0.0.1:8000/metrics/')
    print(r.status_code)
    print(r.text[:1000])
except Exception as e:
    print('ERR', e)

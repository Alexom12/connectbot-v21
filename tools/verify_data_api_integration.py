#!/usr/bin/env python
"""Quick integration verifier for Data API.

Checks:
- DB query counts for first vs second request (shows caching reduces DB load)
- Prometheus metric values for requests/hits/misses
- Attempts an external HTTP call to the running server to simulate Java container

Run with: .\venv\\\Scripts\Activate.ps1; python tools/verify_data_api_integration.py
"""
import os
import json
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import Client
from django.db import connection
from django.test.utils import CaptureQueriesContext, override_settings

from python_app.api import data_api as data_api_module
from django.conf import settings

TEST_TOKEN = 'test-token'
os.environ['SERVICE_AUTH_TOKEN'] = TEST_TOKEN

# Use the token actually configured in Django settings for external requests
EXTERNAL_TOKEN = getattr(settings, 'SERVICE_AUTH_TOKEN', TEST_TOKEN)

body = {'algorithm_type': 'cross_department'}

def print_metric(name, metric):
    try:
        if metric is None:
            print(f"{name}: (not available)")
            return
        # try to read internal value
        val = None
        if hasattr(metric, '_value'):
            val = metric._value.get()
        elif hasattr(metric, 'count'):
            val = metric.count
        print(f"{name}: {val}")
    except Exception as e:
        print(f"{name}: error reading metric: {e}")


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    ALLOWED_HOSTS=['testserver', '127.0.0.1', 'localhost', '*']
)
def run_check():
    client = Client()
    headers = {'HTTP_AUTHORIZATION': f'Service {TEST_TOKEN}'}

    print('Performing first in-process POST (should hit DB)')
    with CaptureQueriesContext(connection) as c1:
        r1 = client.post('/api/v1/data/employees-for-matching', data=json.dumps(body), content_type='application/json', **headers)
    print('Status:', r1.status_code)
    print('DB queries (first):', len(c1))

    print('\nPerforming second in-process POST (should be cached -> fewer DB queries)')
    with CaptureQueriesContext(connection) as c2:
        r2 = client.post('/api/v1/data/employees-for-matching', data=json.dumps(body), content_type='application/json', **headers)
    print('Status:', r2.status_code)
    print('DB queries (second):', len(c2))

    print('\nPrometheus metrics snapshot:')
    print_metric('REQ_COUNTER', getattr(data_api_module, 'REQ_COUNTER', None))
    print_metric('REQ_ERRORS', getattr(data_api_module, 'REQ_ERRORS', None))
    print_metric('CACHE_HITS', getattr(data_api_module, 'CACHE_HITS', None))
    print_metric('CACHE_MISSES', getattr(data_api_module, 'CACHE_MISSES', None))

    # Attempt external HTTP request to running server to simulate Java container
    print('\nAttempting external HTTP call to http://127.0.0.1:8000 (simulate Java)')
    try:
        import requests
        url = 'http://127.0.0.1:8000/api/v1/data/employees-for-matching'
        # Try multiple candidate tokens to match whatever token the running server expects
        candidates = []
        if EXTERNAL_TOKEN:
            candidates.append(EXTERNAL_TOKEN)
        env_tok = os.environ.get('SERVICE_AUTH_TOKEN')
        if env_tok and env_tok not in candidates:
            candidates.append(env_tok)
        if TEST_TOKEN not in candidates:
            candidates.append(TEST_TOKEN)

        success = False
        for tok in candidates:
            headers2 = {'Authorization': f'Service {tok}', 'Content-Type': 'application/json'}
            try:
                resp = requests.post(url, headers=headers2, json=body, timeout=5)
            except Exception as e:
                print('External HTTP call error for token', repr(tok), e)
                continue
            print('Tried token:', repr(tok), '-> status', resp.status_code)
            if resp.status_code == 200:
                success = True
                try:
                    print('External response json keys:', list(resp.json().keys()))
                except Exception:
                    print('External response text length:', len(resp.text or ''))
                break
        if not success:
            print('External request did not succeed with any candidate token. Last status:', resp.status_code if 'resp' in locals() else 'no response')
    except Exception as e:
        print('External HTTP call failed (is runserver running?)', e)


if __name__ == '__main__':
    run_check()

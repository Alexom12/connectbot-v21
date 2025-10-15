import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from bots.services.matching_service_client import MatchingServiceClient
c=MatchingServiceClient()
# increment some in-memory metrics to simulate activity
c.metrics['matching_requests'] += 2
c.metrics['matching_requests_success'] += 1
c.metrics['matching_latency_ms_total'] += 350.5
print('in-memory metrics after increment:', c.get_metrics())

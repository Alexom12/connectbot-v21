import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from bots.services.matching_service_client import MatchingServiceClient

try:
    from prometheus_client import Counter, Histogram
    prom_available = True
except Exception:
    prom_available = False

c = MatchingServiceClient()
inc_used = False
# Prefer using client's registered prometheus metrics if available
if getattr(c, 'prom_matching_requests', None):
    try:
        c.prom_matching_requests.inc(3)
        if getattr(c, 'prom_matching_latency', None):
            c.prom_matching_latency.observe(0.35)
        inc_used = True
        print('Incremented client.prom metrics')
    except Exception as e:
        print('Failed to inc client.prom metrics:', e)

# Fallback: create unique-test metrics to avoid registration name conflicts
if not inc_used and prom_available:
    try:
        test_counter = Counter('cb_test_matching_requests_total', 'Test matching requests total')
        test_hist = Histogram('cb_test_matching_latency_seconds', 'Test matching latency seconds')
        test_counter.inc(3)
        test_hist.observe(0.35)
        print('Created and incremented fallback test prometheus metrics')
    except Exception as e:
        print('Failed to create fallback prometheus metrics:', e)

if not prom_available:
    print('prometheus-client not available in this environment')

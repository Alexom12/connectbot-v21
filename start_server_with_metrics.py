import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

print('Django setup complete in wrapper script')

# Try to increment client's Prometheus metrics in this process
try:
    from bots.services.matching_service_client import MatchingServiceClient
    c = MatchingServiceClient()
    if getattr(c, 'prom_matching_requests', None):
        try:
            c.prom_matching_requests.inc(5)
            if getattr(c, 'prom_matching_latency', None):
                c.prom_matching_latency.observe(0.42)
            print('Incremented client.prom metrics in server process')
        except Exception as e:
            print('Failed to inc client.prom metrics:', e)
    else:
        print('Client prom metrics not present')
except Exception as e:
    print('Error initializing MatchingServiceClient in wrapper:', e)

# Start Django dev server in this process (no autoreload)
from django.core.management import call_command
print('Starting runserver...')
call_command('runserver', '127.0.0.1:8000', use_reloader=False)

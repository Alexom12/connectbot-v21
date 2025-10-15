from prometheus_client import generate_latest
from bots.services.matching_service_client import MatchingServiceClient

# Instantiate client to ensure metrics are registered/updated
c = MatchingServiceClient()
# Optionally simulate a metric change
_ = c.get_metrics()

print(generate_latest().decode('utf-8'))

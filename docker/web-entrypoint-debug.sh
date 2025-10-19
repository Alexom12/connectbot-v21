#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

# Add verbose logging
echo ">>> [web-entrypoint-debug.sh] STARTING IN DEBUG MODE"

echo ">>> [web-entrypoint-debug.sh] Applying Django migrations..."
python manage.py migrate --noinput

echo ">>> [web-entrypoint-debug.sh] Migrations applied. Container will now sleep indefinitely."
echo ">>> Use 'docker exec -it <container_id> /bin/bash' to connect."

# Sleep forever to keep the container running for inspection
sleep infinity

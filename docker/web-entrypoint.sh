#!/bin/sh
# docker/web-entrypoint.sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Add verbose logging
echo ">>> [web-entrypoint.sh] STARTING"

# Add a small delay to allow network to settle
sleep 3

echo ">>> [web-entrypoint.sh] Applying Django migrations..."
python manage.py migrate --noinput

echo ">>> [web-entrypoint.sh] Migrations applied successfully."

# Execute the command passed to this script (e.g., from the Dockerfile's CMD)
echo ">>> [web-entrypoint.sh] Starting main process (exec $@)..."
exec "$@"

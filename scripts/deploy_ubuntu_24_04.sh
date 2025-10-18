#!/usr/bin/env bash
set -euo pipefail

# deploy_ubuntu_24_04.sh
# Usage:
#   sudo bash deploy_ubuntu_24_04.sh [branch] [SERVICE_AUTH_TOKEN]
# Example:
#   sudo bash deploy_ubuntu_24_04.sh main secret_token_123
#
# What it does:
# - Installs Docker and docker-compose-plugin on Ubuntu 24.04 (if missing)
# - Installs git, curl, jq
# - Clones or updates the repository into /opt/connectbot-v21
# - Writes a .env with SERVICE_AUTH_TOKEN and MATCHING_DATAAPI_URL
# - Runs `docker compose -f docker/docker-compose.yml up --build -d`
# - Waits for services, checks basic health endpoint on localhost:8000
# - Writes logs to /var/log/connectbot_deploy/

LOG_DIR="/var/log/connectbot_deploy"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/deploy_$(date +%Y%m%d%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

REPO_URL="https://github.com/Alexom12/connectbot-v21.git"
DEST_DIR="/opt/connectbot-v21"
BRANCH="${1:-main}"
SERVICE_TOKEN="${2:-}"

if [ -z "$SERVICE_TOKEN" ]; then
  # generate a short random token
  if command -v openssl >/dev/null 2>&1; then
    SERVICE_TOKEN="cbtkn_$(openssl rand -hex 8)"
  else
    SERVICE_TOKEN="cbtkn_$(head -c8 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  fi
  echo "SERVICE_AUTH_TOKEN not provided; generated: $SERVICE_TOKEN"
fi

echo "Starting deploy at $(date)"
echo "Branch: $BRANCH"
echo "Destination: $DEST_DIR"

# 1) Basic packages
echo "==> Installing basic packages (git, curl, jq)"
apt update -y
apt install -y git curl jq ca-certificates lsb-release gnupg || true

# 2) Install Docker if missing
if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installing Docker via get.docker.com"
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  rm -f get-docker.sh
else
  echo "docker already installed: $(docker --version)"
fi

# Ensure docker-compose-plugin is installed
if ! docker compose version >/dev/null 2>&1; then
  echo "==> Installing docker compose plugin"
  apt install -y docker-compose-plugin || true
else
  echo "docker compose available: $(docker compose version)"
fi

# Make sure docker daemon is running
if ! systemctl is-active --quiet docker; then
  echo "==> Starting docker daemon"
  systemctl enable --now docker || true
fi

# 3) Clone or update repo
if [ -d "$DEST_DIR/.git" ]; then
  echo "==> Updating existing repository"
  cd "$DEST_DIR"
  git fetch --all --prune
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH" || git pull origin "$BRANCH" || true
else
  echo "==> Cloning repository into $DEST_DIR"
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$DEST_DIR"
fi

cd "$DEST_DIR"

# 4) Write .env
ENV_FILE="$DEST_DIR/.env"
echo "==> Writing .env to $ENV_FILE"
cat > "$ENV_FILE" <<EOF
SERVICE_AUTH_TOKEN=$SERVICE_TOKEN
MATCHING_DATAAPI_URL=http://python-app:8000
EOF

# 5) Run docker compose
COMPOSE_FILE="$DEST_DIR/docker/docker-compose.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "ERROR: compose file not found at $COMPOSE_FILE"
  exit 1
fi

echo "==> Starting docker compose"
# Use sudo for docker commands in case user not in docker group
sudo docker compose -f "$COMPOSE_FILE" up --build -d

# 6) Wait for services to be healthy/running
echo "==> Waiting for containers to appear (timeout 120s)"
RETRIES=0
MAX_RETRIES=24
SLEEP=5
while [ $RETRIES -lt $MAX_RETRIES ]; do
  echo "-- status check #$RETRIES"
  sudo docker compose -f "$COMPOSE_FILE" ps --quiet | xargs -r sudo docker inspect --format '{{.Name}} {{.State.Status}}' || true
  ALL_RUNNING=true
  while read -r cid; do
    if [ -n "$cid" ]; then
      status=$(sudo docker inspect --format '{{.State.Status}}' "$cid" 2>/dev/null || echo "unknown")
      if [ "$status" != "running" ]; then
        ALL_RUNNING=false
      fi
    fi
  done < <(sudo docker compose -f "$COMPOSE_FILE" ps -q)

  if [ "$ALL_RUNNING" = true ]; then
    echo "All containers running"
    break
  fi
  RETRIES=$((RETRIES+1))
  sleep $SLEEP
done

# 7) Basic health check against Data API
# Try localhost:8000 first
echo "==> Performing Data API health check"
HEALTH_URLS=("http://localhost:8000/api/v1/health" "http://127.0.0.1:8000/api/v1/health")
HEALTH_OK=false
for url in "${HEALTH_URLS[@]}"; do
  echo "Checking $url"
  if curl -sS -H "Authorization: Service $SERVICE_TOKEN" "$url" -m 5 | grep -qi "ok"; then
    echo "Health check OK at $url"
    HEALTH_OK=true
    break
  else
    echo "No healthy response at $url"
  fi
done

if [ "$HEALTH_OK" = false ]; then
  echo "Health check failed — dumping container statuses and recent logs"
  sudo docker compose -f "$COMPOSE_FILE" ps
  sudo docker compose -f "$COMPOSE_FILE" logs --tail 200 > "$LOG_DIR/compose_logs_$(date +%Y%m%d%H%M%S).log" || true
  echo "Saved logs to $LOG_DIR"
  echo "You can inspect logs file and the deploy log: $LOG_FILE"
  exit 2
fi

# 8) Success
echo "==> Deployment looks healthy"
sudo docker compose -f "$COMPOSE_FILE" ps
sudo docker compose -f "$COMPOSE_FILE" logs --tail 200

echo "Done. Deploy log: $LOG_FILE"

echo "Notes:
- If you run this script as non-root, some docker commands may require sudo or a new login after adding the user to the docker group.
- To re-run, you can pull latest changes (cd $DEST_DIR && git pull) and re-run docker compose up --build -d
"

exit 0

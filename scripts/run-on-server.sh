#!/usr/bin/env bash
# run-on-server.sh — соберёт matching, соберёт образ, обновит стек и сохранит логи
# Запускать на сервере в каталоге /opt/connectbot-v21 или из любой директории (скрипт использует абсолютные пути).
set -euo pipefail

WORKDIR="/opt/connectbot-v21"
SERVICE_NAME="connectbot"
MATCHING_DIR="$WORKDIR/connectbot-java-services/matching-service"
IMAGE_TAG="alexom12/connectbot-matching-service:debug"
STACK_FILE="$WORKDIR/docker/docker-stack.yml"
MATCHING_SERVICE_FQN="${SERVICE_NAME}_matching-service"
WEB_SERVICE_FQN="${SERVICE_NAME}_web"
OUT_DIR="/tmp/connectbot_logs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT_DIR"

echo "Working directory: $WORKDIR"
cd "$WORKDIR"

echo "Reset to origin/main (fetch + reset)"
git fetch --all --prune
git reset --hard origin/main

echo "Building matching-service (skip tests)"
cd "$MATCHING_DIR"
if [ -x ./mvnw ]; then
  ./mvnw -f pom.xml -DskipTests -Dmaven.test.skip=true package
else
  mvn -DskipTests -Dmaven.test.skip=true package
fi

echo "Building Docker image: $IMAGE_TAG"
cd "$MATCHING_DIR"
docker build -t "$IMAGE_TAG" .

echo "Deploying stack (file: $STACK_FILE)"
cd "$WORKDIR"
docker stack deploy -c "$STACK_FILE" "$SERVICE_NAME"

echo "Forcing update of matching service to pick up new image"
docker service update --force "$MATCHING_SERVICE_FQN" || true

# Wait a bit for tasks to start
echo "Waiting 6s for tasks to converge..."
sleep 6

# Collect logs (last 500 lines or 2 minutes)
echo "Collecting service logs..."
docker service logs "$MATCHING_SERVICE_FQN" --since 2m --tail 500 > "$OUT_DIR/matching.log" 2>&1 || true
docker service logs "$WEB_SERVICE_FQN" --since 2m --tail 500 > "$OUT_DIR/web.log" 2>&1 || true

echo "Saved logs to: $OUT_DIR"
echo
echo "Showing filtered diagnostics (masked tokens / auth diagnostics):"
echo "---- matching (masked token log lines) ----"
grep -E "DataApiClient: sending Authorization header|Loaded Data API service token from file" "$OUT_DIR/matching.log" || echo "(no matching masked lines found)"
echo
echo "---- web (incoming Authorization / Auth failed lines) ----"
grep -E "Incoming Authorization header|Auth failed: received Authorization|Unauthorized" "$OUT_DIR/web.log" || echo "(no web auth diagnostic lines found)"
echo

echo "If you want the full logs, download these files:"
ls -l "$OUT_DIR"
echo
echo "To tail logs live (in two terminals) use:"
echo " docker service logs $MATCHING_SERVICE_FQN --follow --tail 200"
echo " docker service logs $WEB_SERVICE_FQN --follow --tail 200"

echo "Done."

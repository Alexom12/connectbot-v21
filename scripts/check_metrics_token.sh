#!/usr/bin/env bash
set -euo pipefail

if [ -z "${METRICS_TRIGGER_TOKEN-}" ]; then
  echo "METRICS_TRIGGER_TOKEN is not set"
  exit 1
fi
echo "METRICS_TRIGGER_TOKEN is set"

#!/usr/bin/env bash
set -euo pipefail

cd /opt/data/home/workspace/data-analysis

if [ -f /opt/data/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /opt/data/.env
  set +a
fi

exec python3 -m backend.dashboard_chat.server \
  --host "${DASHBOARD_CHAT_HOST:-127.0.0.1}" \
  --port "${DASHBOARD_CHAT_PORT:-8765}"

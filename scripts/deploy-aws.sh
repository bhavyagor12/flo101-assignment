#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.aws.example to .env and fill the API keys." >&2
  exit 1
fi

docker compose -f docker-compose.aws.yml build
docker compose -f docker-compose.aws.yml up -d

echo "Waiting for web healthcheck..."
for _ in $(seq 1 60); do
  if docker compose -f docker-compose.aws.yml ps --format json 2>/dev/null | grep -q '"web".*"healthy"'; then
    break
  fi
  if curl -fsS "http://localhost:${WEB_PORT:-80}/" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

docker compose -f docker-compose.aws.yml ps
echo "Deployed. Open http://<EC2_PUBLIC_IP>:${WEB_PORT:-80}"

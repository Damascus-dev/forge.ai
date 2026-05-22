#!/usr/bin/env bash
set -euo pipefail
# Start Forge stack via Docker Compose
cd "$(dirname "$0")"
docker compose -f docker/docker-compose.yml up -d
echo "Forge stack started!"
echo "API:  http://localhost:8000"
echo "Docs: http://localhost:8000/docs"

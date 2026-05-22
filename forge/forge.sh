#!/usr/bin/env bash
set -euo pipefail
# forge.sh — start/stop/status the Forge backend

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${FORGE_DIR}/logs"
PID_FILE="${LOG_DIR}/forge.pid"
mkdir -p "$LOG_DIR"

case "${1:-help}" in
  start)
    echo "Starting Forge API..."
    cd "$FORGE_DIR"
    source .venv/bin/activate 2>/dev/null || true
    nohup python run.py > "${LOG_DIR}/api.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Forge API started (PID: $(cat "$PID_FILE"))"
    echo "Logs: ${LOG_DIR}/api.log"
    echo "API:  http://localhost:8000"
    echo "Docs: http://localhost:8000/docs"
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      kill "$(cat "$PID_FILE")" 2>/dev/null && echo "Stopped Forge API" || echo "Process already stopped"
      rm -f "$PID_FILE"
    else
      echo "No PID file found. Try: pkill -f 'uvicorn forge.api.main'"
    fi
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "Forge API is running (PID: $(cat "$PID_FILE"))"
    else
      echo "Forge API is not running"
    fi
    ;;
  docker-up)
    cd "$FORGE_DIR"
    docker compose -f docker/docker-compose.yml up -d
    echo "Forge stack started via Docker"
    ;;
  docker-down)
    cd "$FORGE_DIR"
    docker compose -f docker/docker-compose.yml down
    echo "Forge stack stopped"
    ;;
  logs)
    cat "${LOG_DIR}/api.log" 2>/dev/null || echo "No logs found"
    ;;
  test)
    echo "=== Health Check ==="
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "API not reachable"
    echo ""
    echo "=== Running Tests ==="
    cd "$FORGE_DIR"
    source .venv/bin/activate 2>/dev/null
    pytest tests/ -v
    ;;
  *)
    echo "Usage: $0 {start|stop|status|docker-up|docker-down|logs|test}"
    exit 1
    ;;
esac

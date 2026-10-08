#!/usr/bin/env bash
# Launcher for AI Job Search Localhost Web App
PORT=${1:-8000}
echo "Starting AI Job Search Dashboard on http://localhost:$PORT..."

# Open in default browser if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  (sleep 1 && open "http://localhost:$PORT") &
fi

python3 "$(dirname "$0")/server.py" "$PORT"

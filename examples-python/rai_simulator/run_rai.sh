#!/usr/bin/env bash
set -Eeuo pipefail

echo "🧠 Starting RAI Simulator..."

cd "$(dirname "$0")"

# Use same venv as connectors
if [ -d "../gemini-streams-sse-connector/.venv" ]; then
    source ../gemini-streams-sse-connector/.venv/bin/activate
fi

# Kill old instance if port busy
if lsof -i :4545 >/dev/null; then
    echo "⚠️ Port 4545 busy — killing old instance"
    lsof -ti :4545 | xargs kill -9
fi

uvicorn rai_simulator:app --host 127.0.0.1 --port 4545

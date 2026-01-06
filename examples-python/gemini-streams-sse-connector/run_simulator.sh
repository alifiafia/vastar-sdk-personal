#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"

echo "🚀 Starting Gemini Connector with RAI Simulator"

# ===============================
# Activate venv
# ===============================
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export USE_SIMULATOR=true
export GEMINI_API_KEY="DUMMY"

SIM_PID=""
APP_PID=""

shutdown() {
    echo ""
    echo "🧯 Graceful shutdown..."

    if [[ -n "$APP_PID" ]] && kill -0 "$APP_PID" 2>/dev/null; then
        kill -TERM "$APP_PID"
        wait "$APP_PID" 2>/dev/null || true
    fi

    if [[ -n "$SIM_PID" ]] && kill -0 "$SIM_PID" 2>/dev/null; then
        kill -TERM "$SIM_PID"
        wait "$SIM_PID" 2>/dev/null || true
    fi

    echo "✅ Shutdown complete"
    exit 0
}

trap shutdown SIGINT SIGTERM

# ===============================
# Start RAI Simulator
# ===============================
cd ../rai_simulator

if lsof -ti :4545 >/dev/null 2>&1; then
    echo "⚠️ Port 4545 already in use"
    exit 1
fi

echo "🧪 Starting RAI Simulator"
setsid uvicorn rai_simulator:app \
    --host 127.0.0.1 \
    --port 4545 \
    --workers 1 \
    --log-level info \
    --access-log &

SIM_PID=$!

cd - >/dev/null
sleep 2

# ===============================
# Start Gemini Connector
# ===============================
echo "🔌 Starting Gemini Connector"
setsid python3 main.py &
APP_PID=$!

# ===============================
# Supervisor Loop
# ===============================
while true; do
    kill -0 "$SIM_PID" 2>/dev/null || { echo "❌ RAI crashed"; shutdown; }
    kill -0 "$APP_PID" 2>/dev/null || { echo "❌ Connector crashed"; shutdown; }
    sleep 1
done

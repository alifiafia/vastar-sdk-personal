#!/bin/bash
set -e

echo "🚀 Starting Gemini Connector with RAI Simulator..."

cd "$(dirname "$0")"

if [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi

export USE_SIMULATOR=true
export GEMINI_API_KEY="DUMMY"

echo "🧪 Starting RAI Simulator on port 4545..."
uvicorn rai_simulator:app --host 0.0.0.0 --port 4545 --workers 4 &
SIM_PID=$!

sleep 2

echo "🔌 Starting Gemini Connector..."
python3 main.py   # <-- TIDAK di-background-kan

echo "🛑 Stopping..."
kill $SIM_PID

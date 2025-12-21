#!/bin/bash
# Start Vastar Connector Runtime

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_PATH="$SCRIPT_DIR/connector-runtime/vastar-connector-runtime"

# Clean up old instances first
if [ -f "$SCRIPT_DIR/clean_vcr.sh" ]; then
    "$SCRIPT_DIR/clean_vcr.sh"
    echo ""
fi

echo "🚀 Starting Vastar Connector Runtime..."

if [ ! -f "$RUNTIME_PATH" ]; then
    echo "❌ Runtime not found: $RUNTIME_PATH"
    exit 1
fi

chmod +x "$RUNTIME_PATH"

# Start runtime
"$RUNTIME_PATH" > /tmp/vastar-runtime.log 2>&1 &
RUNTIME_PID=$!

sleep 2

if kill -0 $RUNTIME_PID 2>/dev/null; then
    echo "✅ Runtime started (PID: $RUNTIME_PID)"
    echo "   Socket: /tmp/vastar-connector-runtime.sock"
else
    echo "❌ Failed to start runtime"
    cat /tmp/vastar-runtime.log
    exit 1
fi


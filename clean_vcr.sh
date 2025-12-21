#!/bin/bash
# Clean Vastar Connector Runtime instances

echo "🧹 Cleaning Vastar Connector Runtime instances..."

# Find all vastar-connector-runtime processes
PIDS=$(pgrep -f vastar-connector-runtime)

if [ -z "$PIDS" ]; then
    echo "✅ No runtime instances found"
else
    echo "Found running instances:"
    ps aux | grep vastar-connector-runtime | grep -v grep
    echo ""
    echo "Killing processes..."

    for PID in $PIDS; do
        echo "  Killing PID: $PID"
        kill -9 $PID 2>/dev/null
    done

    sleep 1

    # Verify all killed
    REMAINING=$(pgrep -f vastar-connector-runtime)
    if [ -z "$REMAINING" ]; then
        echo "✅ All runtime instances stopped"
    else
        echo "⚠️  Some instances still running:"
        ps aux | grep vastar-connector-runtime | grep -v grep
    fi
fi

# Clean up socket file
if [ -S /tmp/vastar-connector-runtime.sock ]; then
    echo "Removing socket file..."
    rm -f /tmp/vastar-connector-runtime.sock
    echo "✅ Socket file removed"
fi

# Clean up log file
if [ -f /tmp/vastar-runtime.log ]; then
    echo "Removing log file..."
    rm -f /tmp/vastar-runtime.log
    echo "✅ Log file removed"
fi

echo ""
echo "🎉 Cleanup complete!"


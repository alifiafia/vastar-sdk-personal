#!/bin/bash

# Run Java OpenAI SSE Connector with Simulator

set -e

cd "$(dirname "$0")"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║     🚀 Java OpenAI Stream SSE Connector - Simulator Mode    ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "📋 Checking Prerequisites..."
echo ""

# Check Vastar Runtime
if pgrep -x vastar-connector-runtime > /dev/null; then
    echo "✅ Vastar Runtime: Running"
else
    echo "❌ Vastar Runtime: Not running"
    echo ""
    echo "Please start the runtime first:"
    echo "  cd ../../.."
    echo "  ./start_runtime.sh"
    echo ""
    exit 1
fi

# Check socket
if [ -S /tmp/vastar-connector-runtime.sock ]; then
    echo "✅ Unix Socket: Found"
else
    echo "❌ Unix Socket: Not found"
    exit 1
fi

# Check RAI Simulator
if docker ps | grep -q rai-simulator; then
    echo "✅ RAI Simulator: Running"
else
    echo "❌ RAI Simulator: Not running"
    echo ""
    echo "Starting RAI Simulator..."
    docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

    echo "⏳ Waiting for simulator to start..."
    sleep 3

    if docker ps | grep -q rai-simulator; then
        echo "✅ RAI Simulator: Started"
    else
        echo "❌ Failed to start simulator"
        exit 1
    fi
fi

# Test simulator API
if curl -sf -X POST http://localhost:4545/test_completion > /dev/null 2>&1; then
    echo "✅ Simulator API: Responding"
else
    echo "❌ Simulator API: Not responding"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🚀 Running Java OpenAI Connector..."
echo ""

# Run with Gradle
./gradlew --no-daemon runSimulator

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Example completed!"
echo ""


# 🔧 Setup Guide

**Complete installation guide for Vastar Runtime and RAI Endpoint Simulator**

---

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Helper Scripts](#helper-scripts)
- [Vastar Runtime Setup](#vastar-runtime-setup)
- [RAI Simulator Setup](#rai-simulator-setup)
  - [Method 1: Docker (Recommended)](#method-1-docker-recommended)
  - [Method 2: From Source](#method-2-from-source)
- [Verification](#verification)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## 💻 System Requirements

### Required

- **Go 1.21+** - For running examples
- **Linux/macOS** - Unix socket support (Windows uses TCP)
- **Git** - For cloning repositories

### For Docker Setup

- **Docker** - For running simulator in container

### For Source Build

- **Rust 1.70+** - For building RAI Simulator
- **Cargo** - Rust package manager

---

## 🛠️ Helper Scripts

The repository includes helper scripts in the root directory:

### `start_runtime.sh`

Starts the Vastar Connector Runtime with automatic cleanup.

```bash
./start_runtime.sh
```

**What it does:**
1. Calls `clean_vcr.sh` to clean up old instances
2. Removes old socket files
3. Starts a fresh runtime instance
4. Verifies it started successfully
5. Shows PID and socket path

### `clean_vcr.sh`

Cleans up all Vastar Connector Runtime instances.

```bash
./clean_vcr.sh
```

**What it does:**
1. Finds all running runtime processes
2. Kills all instances
3. Removes socket file (`/tmp/vastar-connector-runtime.sock`)
4. Removes log file (`/tmp/vastar-runtime.log`)

**When to use:**
- Before starting a fresh runtime
- When you have multiple runtime instances
- When socket file is corrupted
- When troubleshooting connection issues

---

## 🚀 Vastar Runtime Setup

### Step 1: Build Runtime

```bash
# From repository root
cd vastar-wf-connector-sdk-bin

# Build Rust runtime
cargo build --release

# Binary will be at: target/release/vastar-connector-runtime
# Or pre-built at: connector-runtime/vastar-connector-runtime
```

### Step 2: Start Runtime

**Recommended: Using Helper Script**

```bash
# From repository root
./start_runtime.sh
```

This script will automatically:
- Clean up any old runtime instances (calls `clean_vcr.sh`)
- Remove old socket files
- Start a fresh runtime instance
- Verify it started successfully

**Manual Start (Alternative)**

If you need to manually clean up first:

```bash
# Clean up old instances
./clean_vcr.sh

# Then start runtime manually
cd connector-runtime
./vastar-connector-runtime > /tmp/vastar-runtime.log 2>&1 &
```

### Step 3: Verify Runtime

```bash
# Check process
pgrep -a vastar-connector-runtime
# Expected: [PID] ./vastar-connector-runtime

# Check socket (Linux/macOS)
ls -la /tmp/vastar-connector-runtime.sock
# Expected: srwxrwxr-x ... /tmp/vastar-connector-runtime.sock

# Check TCP port (Windows)
netstat -an | grep 5000
# Expected: TCP 0.0.0.0:5000 LISTENING
```

### Step 4: Test Runtime

```bash
# Quick test with SDK
cd examples-golang/openai-stream-sse-connector
go run -tags test_runtime << 'EOF'
package main
import (
    "fmt"
    "log"
    vastar "github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang"
)
func main() {
    client, err := vastar.NewRuntimeClient()
    if err != nil {
        log.Fatal(err)
    }
    defer client.Close()
    fmt.Println("✅ Runtime connection successful!")
}
EOF
```

---

## 🎯 RAI Simulator Setup

RAI Endpoint Simulator is an OpenAI-compatible API server for testing and development.

**Repository:** https://github.com/fullstack-aidev/rai-endpoint-simulator

### Method 1: Docker (Recommended)

**Fastest and easiest method for development.**

#### Option A: Pull Pre-built Image

```bash
# Pull image (if available)
docker pull fullstackaidev/rai-endpoint-simulator:latest

# Run container
docker run -d \
  --name rai-simulator \
  -p 4545:4545 \
  fullstackaidev/rai-endpoint-simulator:latest

# Check logs
docker logs rai-simulator
# Expected: Server running at http://0.0.0.0:4545
```

#### Option B: Build from Source

```bash
# Clone repository
git clone https://github.com/fullstack-aidev/rai-endpoint-simulator.git
cd rai-endpoint-simulator

# Build Docker image
docker build -t rai-endpoint-simulator:latest .

# Run container
docker run -d \
  --name rai-simulator \
  -p 4545:4545 \
  rai-endpoint-simulator:latest
```

#### Docker with Custom Configuration

```bash
# Create custom config.yml
cat > config.yml << 'EOF'
source: "file"
log_level: "info"
channel_capacity: 1000
semaphore_limit: 100

binding:
  host: "0.0.0.0"
  port: 4545

tracking:
  enabled: true
EOF

# Run with custom config
docker run -d \
  --name rai-simulator \
  -p 4545:4545 \
  -v $(pwd)/config.yml:/app/config.yml \
  rai-endpoint-simulator:latest
```

#### Docker with Custom Response Files

```bash
# Create response directory
mkdir zresponse

# Add custom responses
cat > zresponse/custom_response.md << 'EOF'
This is a custom AI response for testing.
It will be streamed character by character.
You can add multiple response files here.
EOF

# Run with custom responses
docker run -d \
  --name rai-simulator \
  -p 4545:4545 \
  -v $(pwd)/config.yml:/app/config.yml \
  -v $(pwd)/zresponse:/app/zresponse \
  rai-endpoint-simulator:latest
```

#### Docker Management Commands

```bash
# Check container status
docker ps | grep rai-simulator

# View logs
docker logs -f rai-simulator

# Stop container
docker stop rai-simulator

# Start container
docker start rai-simulator

# Remove container
docker rm -f rai-simulator

# Access container shell
docker exec -it rai-simulator /bin/sh
```

---

### Method 2: From Source

**For development and customization.**

#### Step 1: Install Rust

```bash
# Install Rust (if not already)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify installation
rustc --version
cargo --version
```

#### Step 2: Clone Repository

```bash
git clone https://github.com/fullstack-aidev/rai-endpoint-simulator.git
cd rai-endpoint-simulator
```

#### Step 3: Build Simulator

```bash
# Debug build (faster compilation)
cargo build

# Release build (optimized)
cargo build --release
```

#### Step 4: Configure Simulator

```bash
# Copy example config
cp config.example.yml config.yml

# Edit configuration
nano config.yml
```

Example `config.yml`:

```yaml
# Data source: "file" or "database"
source: "file"

# Logging level: "trace", "debug", "info", "warn", "error"
log_level: "info"

# SSE channel capacity
channel_capacity: 1000

# Concurrent request limit
semaphore_limit: 100

# Server binding
binding:
  host: "0.0.0.0"
  port: 4545

# Request tracking
tracking:
  enabled: true

# File source configuration
file_source:
  directory: "./zresponse"
  pattern: "*.md"

# Database source configuration (optional)
database:
  url: "postgresql://user:pass@localhost/dbname"
  max_connections: 10
```

#### Step 5: Add Response Files

```bash
# Create response directory
mkdir -p zresponse

# Add sample responses
cat > zresponse/quantum_computing.md << 'EOF'
Quantum computing is a revolutionary approach to computation that leverages 
the principles of quantum mechanics. Unlike classical computers that use bits 
(0 or 1), quantum computers use quantum bits or "qubits" which can exist in 
multiple states simultaneously due to superposition.
EOF

cat > zresponse/go_programming.md << 'EOF'
Go is a statically typed, compiled programming language designed at Google. 
It combines the efficiency of compiled languages with the ease of programming 
of dynamic languages. Go is known for its simplicity, strong concurrency 
support, and excellent performance.
EOF
```

#### Step 6: Run Simulator

```bash
# Run in foreground (debug)
cargo run --release

# Or run binary directly
./target/release/rai-endpoint-simulator

# Run in background
nohup cargo run --release > simulator.log 2>&1 &

# Or with specific config
./target/release/rai-endpoint-simulator --config custom_config.yml
```

---

## ✅ Verification

### Test Vastar Runtime

```bash
# Check if socket exists (Linux/macOS)
ls -la /tmp/vastar-connector-runtime.sock
# Expected: srwxrwxr-x ... /tmp/vastar-connector-runtime.sock

# Check process
ps aux | grep vastar-connector-runtime
```

### Test RAI Simulator

#### Test Connection

```bash
curl -X POST http://localhost:4545/test_completion
```

**Expected Response:**
```json
{
  "id": "chatcmpl-test-123",
  "object": "chat.completion",
  "created": 1734789012,
  "model": "test-model",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "============>> Selamat! Aplikasi anda telah sukses terhubung dengan RAI Endpoint Simulator..."
    },
    "finish_reason": "stop"
  }]
}
```

#### Test Streaming Endpoint

```bash
curl -X POST http://localhost:4545/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, AI!"}
    ],
    "stream": true
  }'
```

**Expected Response (SSE stream):**
```
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":1734789012,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"H"},"finish_reason":null}]}

data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":1734789012,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"e"},"finish_reason":null}]}

...

data: [DONE]
```

### Test Complete Stack

```bash
# Run the example
cd examples-golang/openai-stream-sse-connector
go run main.go
```

**Expected Output:**
```
🤖 OpenAI Stream Connector Demo
=============================================================

🐧 Connected via Unix Socket: /tmp/vastar-connector-runtime.sock
📡 Testing connection to OpenAI Simulator...
✅ ============>> Selamat! Aplikasi anda telah sukses terhubung...
```

---

## ⚙️ Configuration

### Vastar Runtime Configuration

Runtime uses environment variables:

```bash
# Unix socket path (Linux/macOS)
export VASTAR_SOCKET_PATH=/tmp/vastar-connector-runtime.sock

# TCP port (Windows or override)
export VASTAR_TCP_PORT=5000

# Force TCP mode
export VASTAR_USE_TCP=true

# Timeout (seconds)
export VASTAR_TIMEOUT=30
```

### RAI Simulator Configuration

Edit `config.yml`:

```yaml
# Change port
binding:
  host: "0.0.0.0"
  port: 8080  # Custom port

# Increase capacity
channel_capacity: 2000
semaphore_limit: 200

# Enable database source
source: "database"
database:
  url: "postgresql://localhost/rai_db"
  max_connections: 20
```

### Example Configuration

Update `main.go` to match your setup:

```go
// Change simulator URL
connector, err := NewOpenAIConnector("http://localhost:8080")

// Change timeout
httpReq := vastar.POST(url).
    WithTimeout(600000) // 10 minutes
```

---

## 🐛 Troubleshooting

### Runtime Issues

#### Runtime won't start

```bash
# Use the cleanup script
./clean_vcr.sh

# Then start fresh
./start_runtime.sh
```

#### Multiple runtime instances running

```bash
# Check how many instances are running
pgrep -a vastar-connector-runtime

# Clean up all instances
./clean_vcr.sh

# Start a single fresh instance
./start_runtime.sh
```

#### Socket permission denied

The `start_runtime.sh` script automatically handles socket cleanup. If you still have issues:

```bash
# Manual cleanup
./clean_vcr.sh

# Check socket is removed
ls -la /tmp/vastar-connector-runtime.sock

# Restart runtime
./start_runtime.sh
```

### Simulator Issues

#### Port already in use

```bash
# Check what's using port
lsof -i :4545

# Kill process using port
kill -9 $(lsof -t -i :4545)

# Or change simulator port in config.yml
```

#### Docker container won't start

```bash
# Check container logs
docker logs rai-simulator

# Remove and recreate
docker rm -f rai-simulator
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

# Check port mapping
docker port rai-simulator
```

#### Response files not found

```bash
# Check directory exists
ls -la zresponse/

# Create if missing
mkdir -p zresponse
echo "Test response" > zresponse/test.md

# Restart simulator
docker restart rai-simulator
```

### Connection Issues

#### Cannot connect to runtime

```bash
# Verify runtime is running
pgrep -a vastar-connector-runtime

# Check socket exists
ls -la /tmp/vastar-connector-runtime.sock

# Try TCP mode instead
export VASTAR_USE_TCP=true
export VASTAR_TCP_PORT=5000
```

#### Cannot connect to simulator

```bash
# Test with curl
curl -v http://localhost:4545/test_completion

# Check firewall
sudo ufw status
sudo ufw allow 4545

# Check Docker networking
docker inspect rai-simulator | grep IPAddress
```

---


## 📚 Additional Resources

- **Vastar SDK Documentation:** [../../sdk-golang/README.md](../../sdk-golang/README.md)
- **Connector Developer Guide:** [../../sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md](../../sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md)
- **RAI Simulator Repository:** https://github.com/fullstack-aidev/rai-endpoint-simulator
- **Example Code:** [main.go](./main.go)
- **Examples & Tests:** [EXAMPLES.md](./EXAMPLES.md)



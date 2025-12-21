# 🚀 Vastar Workflow Connector SDK

**High-performance connector framework for integrating external APIs with FlatBuffers IPC**

[![Go Version](https://img.shields.io/badge/Go-1.21+-00ADD8?style=flat&logo=go)](https://golang.org/)
[![Rust](https://img.shields.io/badge/Rust-2024-orange?style=flat&logo=rust)](https://www.rust-lang.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📋 Overview

Vastar Workflow Connector SDK is a production-ready framework for building high-performance connectors that integrate external APIs, databases, and services. It uses FlatBuffers for efficient IPC (Inter-Process Communication) between your application and the connector runtime.

### ✨ Key Features

- ✅ **High Performance** - FlatBuffers-based IPC with sub-millisecond overhead
- ✅ **Connection Pooling** - Automatic connection reuse and management
- ✅ **Circuit Breaker** - Prevent cascading failures
- ✅ **Retry Logic** - Automatic retry with exponential backoff
- ✅ **Rate Limiting** - Prevent API quota exhaustion
- ✅ **Multi-tenancy** - Tenant & workspace isolation
- ✅ **Streaming Support** - Server-Sent Events (SSE) streaming
- ✅ **Type Safety** - Strongly typed APIs
- ✅ **Zero Copy** - Efficient memory usage with FlatBuffers

### 🎯 Use Cases

- Building API integrations for workflow automation
- Creating chatbot connectors with streaming support
- Integrating third-party services (OpenAI, databases, etc.)
- High-throughput data processing pipelines
- Multi-tenant SaaS applications

---

## 📦 What's Included

### 1. Connector Runtime (`connector-runtime/`)

Pre-built binary that handles:
- IPC communication via Unix socket
- HTTP/HTTPS requests with connection pooling
- Circuit breaker and retry logic
- Rate limiting and quota management
- Multi-tenant request isolation

**Binary:** `connector-runtime/vastar-connector-runtime`

### 2. Language SDKs

Production-ready client libraries for multiple programming languages:

#### ✅ Available Now: Go SDK (`sdk-golang/`)
- Simple, idiomatic Go API
- Type-safe request/response handling
- Automatic reconnection
- Context propagation
- Comprehensive error handling

**Documentation:**
- [`sdk-golang/README.md`](sdk-golang/README.md) - API Reference
- [`sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md`](sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md) - Complete Guide

#### 🔜 Coming Soon: Additional Language SDKs

We are actively developing SDKs for 10 additional programming languages:

1. **Python SDK** - For data science and ML workflows
2. **JavaScript/TypeScript/Node.js SDK** - For Node.js backend and frontend applications
3. **Java SDK** - For enterprise applications
4. **C# SDK** - For .NET applications
5. **Rust SDK** - For high-performance systems
6. **PHP SDK** - For web applications
7. **Ruby SDK** - For web services
8. **Kotlin SDK** - For Android and backend applications
9. **C/C++ SDK** - For embedded systems and high-performance computing
10. **Groovy SDK** - For JVM-based scripting and automation

All SDKs will provide the same core features:
- ✅ FlatBuffers IPC communication
- ✅ Connection pooling via runtime
- ✅ Type-safe APIs
- ✅ Error handling with retry logic
- ✅ Streaming support (SSE)
- ✅ Multi-tenancy support

**Timeline:** SDKs will be released progressively over the coming months. Follow the repository for updates.

### 3. Examples (`examples-golang/`)

Working examples demonstrating real-world usage:

#### OpenAI Stream Connector (`examples-golang/openai-stream-sse-connector/`)
- Streaming chat completions with SSE
- Non-streaming request-response mode
- Connection testing and error handling
- Switch between simulator and real OpenAI API

**Documentation:**
- [`examples-golang/openai-stream-sse-connector/README.md`](examples-golang/openai-stream-sse-connector/README.md) - Complete guide
- [`examples-golang/openai-stream-sse-connector/SETUP.md`](examples-golang/openai-stream-sse-connector/SETUP.md) - Setup instructions
- [`examples-golang/openai-stream-sse-connector/EXAMPLES.md`](examples-golang/openai-stream-sse-connector/EXAMPLES.md) - Code examples

### 4. Helper Scripts

- **`start_runtime.sh`** - Start runtime with auto-cleanup
- **`clean_vcr.sh`** - Clean up runtime instances

---

## 🚀 Quick Start

### Prerequisites

- **Go 1.21+** - [Download](https://golang.org/dl/)
- **Linux/macOS** - Unix socket support required

### 30-Second Setup

```bash
# 1. Clone the repository
git clone https://github.com/fullstack-aidev/vastar-wf-connector-sdk-bin.git
cd vastar-wf-connector-sdk-bin

# 2. Start the runtime
./start_runtime.sh

# 3. Run the example
cd examples-golang/openai-stream-sse-connector
go run main.go
```

### Your First Connector

Create a file `my-connector.go`:

```go
package main

import (
    "fmt"
    "log"
    
    vastar "github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang"
)

func main() {
    // Connect to runtime
    client, err := vastar.NewRuntimeClient()
    if err != nil {
        log.Fatalf("Failed to connect: %v", err)
    }
    defer client.Close()
    
    // Make HTTP request
    req := vastar.GET("https://api.github.com/zen")
    
    resp, err := client.ExecuteHTTP(req)
    if err != nil {
        log.Fatalf("Request failed: %v", err)
    }
    
    fmt.Printf("Response: %s\n", resp.Body)
}
```

Run it:

```bash
go run my-connector.go
```

---

## 📚 Documentation

### For Developers

1. **[Go SDK README](sdk-golang/README.md)** - API reference and quick examples
2. **[Connector Developer Guide](sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md)** - Complete guide for building connectors

### Examples

1. **[OpenAI Stream Connector](examples-golang/openai-stream-sse-connector/README.md)** - Streaming chat with SSE
2. **[Setup Guide](examples-golang/openai-stream-sse-connector/SETUP.md)** - Environment setup
3. **[Code Examples](examples-golang/openai-stream-sse-connector/EXAMPLES.md)** - Usage patterns

### Architecture

```
┌─────────────────┐
│  Your App (Go)  │
└────────┬────────┘
         │ FlatBuffers IPC
         │ (Unix Socket)
┌────────▼────────────────┐
│  Vastar Runtime (Rust)  │
│  - Connection Pool      │
│  - Circuit Breaker      │
│  - Rate Limiting        │
│  - Retry Logic          │
└────────┬────────────────┘
         │ HTTP/HTTPS
┌────────▼────────┐
│  External APIs  │
│  - OpenAI       │
│  - Databases    │
│  - Services     │
└─────────────────┘
```

---

## 🛠️ Helper Scripts

### `start_runtime.sh`

Starts the Vastar runtime with automatic cleanup:

```bash
./start_runtime.sh
```

Features:
- Automatically kills old runtime instances
- Cleans up stale socket files
- Starts fresh runtime in background
- Verifies successful startup

### `clean_vcr.sh`

Cleans up all runtime instances:

```bash
./clean_vcr.sh
```

Actions:
- Kills all `vastar-connector-runtime` processes
- Removes Unix socket file
- Cleans up log files

Use this when:
- Runtime becomes unresponsive
- Socket file is stale
- Before restarting runtime

---

## 🏗️ Project Structure

```
vastar-wf-connector-sdk-bin/
├── README.md                       # This file
├── Cargo.toml                      # Rust runtime build config
├── start_runtime.sh                # Start runtime helper
├── clean_vcr.sh                    # Cleanup helper
│
├── connector-runtime/              # Pre-built runtime binary
│   └── vastar-connector-runtime    # Linux x86_64 binary
│
├── sdk-golang/                     # Go SDK
│   ├── README.md                   # API reference
│   ├── CONNECTOR_DEVELOPER_GUIDE.md # Complete guide
│   ├── client.go                   # Main SDK implementation
│   ├── go.mod                      # Go module definition
│   ├── protocol/                   # Generated FlatBuffers code
│   │   └── connector_ipc_generated.go
│   └── schemas/                    # FlatBuffers schema
│       └── connector_ipc.fbs
│
├── examples-golang/                # Working examples
│   └── openai-stream-sse-connector/
│       ├── README.md               # Example overview
│       ├── SETUP.md                # Setup instructions
│       ├── EXAMPLES.md             # Code examples
│       ├── config.example.yaml     # Configuration template
│       ├── main.go                 # Example implementation
│       └── go.mod                  # Dependencies
│
└── src/                            # Runtime source (Rust)
    └── main.rs                     # Runtime implementation
```

---

## 🔧 Building from Source

### Runtime (Rust)

```bash
# Build release binary
cargo build --release

# Copy to connector-runtime directory
cp target/release/vastar-wf-connector-sdk-bin connector-runtime/vastar-connector-runtime
```

### Regenerate FlatBuffers Schema (Optional)

```bash
# Install flatc compiler
# Ubuntu/Debian: sudo apt install flatbuffers-compiler
# macOS: brew install flatbuffers

# Regenerate Go code
cd sdk-golang/schemas
flatc --go -o ../protocol connector_ipc.fbs
```

---

## 🧪 Running Examples

### OpenAI Stream Example (with Simulator)

```bash
# 1. Start runtime
./start_runtime.sh

# 2. Start RAI simulator (Docker)
docker run -d --name rai-simulator \
    -p 4545:4545 \
    ghcr.io/fullstack-aidev/rai-endpoint-simulator:latest

# 3. Run example (simulator mode)
cd examples-golang/openai-stream-sse-connector
go run main.go
```

### OpenAI Stream Example (with Real OpenAI API)

```bash
# 1. Start runtime
./start_runtime.sh

# 2. Set OpenAI API key
export OPENAI_API_KEY="sk-..."

# 3. Update config.example.yaml
cp config.example.yaml config.yaml
# Edit config.yaml: set use_real_openai: true

# 4. Run example
cd examples-golang/openai-stream-sse-connector
go run main.go
```

---

## 🐛 Troubleshooting

### Runtime won't start

```bash
# Check if socket file exists
ls -la /tmp/vastar-connector-runtime.sock

# Clean up and restart
./clean_vcr.sh
./start_runtime.sh

# Check logs
tail -f /tmp/vastar-runtime.log
```

### Cannot connect to runtime

```bash
# Verify runtime is running
pgrep -a vastar-connector-runtime

# Check socket permissions
ls -la /tmp/vastar-connector-runtime.sock

# Restart runtime
./clean_vcr.sh
./start_runtime.sh
```

### Go module errors

```bash
# For local development, use replace directive in go.mod:
replace github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang => ../../sdk-golang

# Update dependencies
go mod tidy
```

---

## 🎯 Development Workflow

### 1. Start Development Environment

```bash
# Terminal 1: Start runtime
./start_runtime.sh
tail -f /tmp/vastar-runtime.log

# Terminal 2: Your connector development
cd examples-golang/openai-stream-sse-connector
go run main.go
```

### 2. Make Changes

Edit your connector code and runtime will automatically handle new connections.

### 3. Test

```bash
# Run tests
go test -v ./...

# Build
go build -o my-connector main.go
```

### 4. Deploy

```bash
# Build release binary
go build -ldflags="-s -w" -o my-connector main.go

# Deploy with runtime
scp my-connector user@server:/opt/connectors/
scp connector-runtime/vastar-connector-runtime user@server:/opt/connectors/
```

---

## 📊 Performance

### Benchmarks

- **IPC Overhead**: < 100 microseconds
- **Connection Reuse**: Up to 10x faster than creating new connections
- **Memory Usage**: ~5MB base runtime + connection pool
- **Throughput**: 10,000+ requests/second (with connection pooling)

### Best Practices

1. **Reuse Client**: Create one client, use for multiple requests
2. **Connection Pooling**: Automatically handled by runtime
3. **Batch Requests**: Group related requests when possible
4. **Async Operations**: Use goroutines for concurrent requests
5. **Error Handling**: Always check error classification for retry logic

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🗺️ SDK Roadmap

### Current Status

| Language | Status | Timeline |
|----------|--------|----------|
| **Go** | ✅ Available | Now |
| Python | 🔜 In Development | Q1 2026 |
| JavaScript/TypeScript/Node.js | 🔜 In Development | Q1 2026 |
| Java | 🔜 Planned | Q2 2026 |
| C# | 🔜 Planned | Q2 2026 |
| Rust | 🔜 Planned | Q2 2026 |
| PHP | 🔜 Planned | Q2 2026 |
| Ruby | 🔜 Planned | Q3 2026 |
| Kotlin | 🔜 Planned | Q3 2026 |
| C/C++ | 🔜 Planned | Q3 2026 |
| Groovy | 🔜 Planned | Q3 2026 |

### Why Multiple SDKs?

All SDKs communicate with the same Vastar Connector Runtime using FlatBuffers IPC:

- ✅ **Consistent API** - Same concepts across all languages
- ✅ **High Performance** - FlatBuffers ensures efficient serialization
- ✅ **Language-Idiomatic** - Each SDK follows language best practices
- ✅ **Interoperability** - Mix and match SDKs in microservices
- ✅ **Single Runtime** - One runtime binary serves all SDK clients

**Example:** A Python ML service and a Go API gateway can both use the same runtime instance for API calls, connection pooling, and circuit breaking.

---

## 🆘 Support

- **Documentation**: See [`sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md`](sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md)
- **Examples**: Check [`examples-golang/`](examples-golang/)
- **Issues**: Report bugs via GitHub Issues

---

## 🎓 Next Steps

1. **Read the [Connector Developer Guide](sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md)** - Learn connector development
2. **Try the [OpenAI Example](examples-golang/openai-stream-sse-connector/README.md)** - See streaming in action
3. **Build Your Connector** - Start with the quick start template above
4. **Deploy to Production** - Use systemd or Docker deployment

---

**Ready to build high-performance connectors? Start with the [Quick Start](#-quick-start) guide above!** 🚀


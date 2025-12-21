# 🤖 OpenAI Stream Connector Example

**Streaming Chat Completions with OpenAI-compatible API using Vastar Connector SDK**

[![Go Version](https://img.shields.io/badge/Go-1.21+-00ADD8?style=flat&logo=go)](https://golang.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📋 Overview

This example demonstrates how to build a production-ready OpenAI-compatible connector with streaming support using the Vastar Connector SDK. It communicates with the RAI Endpoint Simulator, which emulates the OpenAI Chat Completions API.

### ✨ Features

- ✅ **Real-time Streaming** - Server-Sent Events (SSE) based streaming
- ✅ **Non-streaming Mode** - Traditional request-response pattern
- ✅ **Connection Testing** - Verify connectivity before operations
- ✅ **Conversation History** - Multi-turn conversations with context
- ✅ **Error Handling** - Robust error handling with retries
- ✅ **Type Safety** - Strongly typed Go structs for requests/responses
- ✅ **Channel-based** - Idiomatic Go concurrency patterns

### 🎯 Use Cases

- Building chatbots with streaming responses
- Integrating OpenAI-compatible APIs
- Learning IPC communication patterns
- Testing with mock AI endpoints
- Developing real-time AI applications

---

## 🚀 Quick Start

### Prerequisites

1. **Go 1.21+** - [Download](https://golang.org/dl/)
2. **Vastar Runtime** - From repository root
3. **RAI Simulator** - OpenAI-compatible mock server

### 3-Step Setup

#### Step 1: Start Vastar Runtime

```bash
# From repository root
cd ../..
./start_runtime.sh

# This will automatically:
# - Clean up any old runtime instances
# - Start a fresh runtime
# - Create socket at /tmp/vastar-connector-runtime.sock
```

Verify it's running:
```bash
ls -la /tmp/vastar-connector-runtime.sock
# Expected: srwxrwxr-x ... /tmp/vastar-connector-runtime.sock
```

#### Step 2: Start RAI Simulator

**Option A: Docker (Recommended)**

```bash
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

# Verify
curl -X POST http://localhost:4545/test_completion
```

**Option B: From Source**

```bash
git clone https://github.com/fullstack-aidev/rai-endpoint-simulator.git
cd rai-endpoint-simulator
cargo run --release
```

See [SETUP.md](./SETUP.md) for detailed installation instructions.

#### Step 3: Run the Example

```bash
# From this directory
go run main.go
```

### Expected Output

```
🤖 OpenAI Stream Connector Demo
=============================================================

🐧 Connected via Unix Socket: /tmp/vastar-connector-runtime.sock
📡 Testing connection to OpenAI Simulator...
✅ ============>> Selamat! Aplikasi anda telah sukses terhubung...

Example 1: Streaming Chat Completion
-------------------------------------------------------------
User: Explain quantum computing in simple terms.
AI: [Streaming response character-by-character]
Quantum computing is a revolutionary approach to computation...
[DONE in 2.3s]

Example 2: Non-Streaming Mode (Collect All)
-------------------------------------------------------------
User: What are the benefits of Go programming?
AI: [Complete response at once]
Go offers several key benefits...
[DONE in 1.8s]

Example 3: Conversation with History
-------------------------------------------------------------
User: Who invented the computer?
AI: Charles Babbage is credited with...

User: Tell me more about his inventions.
AI: Babbage designed the Analytical Engine...
[DONE in 3.1s]

✅ All examples completed successfully!
```

---

## 📚 Usage

### Basic Streaming Example

```go
package main

import (
    "fmt"
    "log"
    vastar "github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang"
)

func main() {
    // Create connector
    connector, err := NewOpenAIConnector("http://localhost:4545")
    if err != nil {
        log.Fatal(err)
    }
    defer connector.Close()

    // Test connection
    msg, err := connector.TestConnection()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("✅ %s\n", msg)

    // Create chat request
    req := ChatCompletionRequest{
        Model: "gpt-4",
        Messages: []Message{
            {Role: "user", Content: "Hello, AI!"},
        },
        Stream: true,
    }

    // Stream response
    chunks, errors := connector.ChatCompletionStream(req)
    
    for {
        select {
        case chunk, ok := <-chunks:
            if !ok {
                goto done
            }
            fmt.Print(chunk)
        case err := <-errors:
            if err != nil {
                log.Fatal(err)
            }
        }
    }
done:
    fmt.Println("\n[DONE]")
}
```

### Non-Streaming Example

```go
// Collect all chunks into one response
content, err := connector.ChatCompletion(ChatCompletionRequest{
    Model: "gpt-4",
    Messages: []Message{
        {Role: "user", Content: "Explain AI briefly"},
    },
    Stream: false,
})

if err != nil {
    log.Fatal(err)
}

fmt.Printf("AI: %s\n", content)
```

### Conversation with History

```go
messages := []Message{
    {Role: "user", Content: "What is Go?"},
}

// First turn
content1, _ := connector.ChatCompletion(ChatCompletionRequest{
    Model:    "gpt-4",
    Messages: messages,
})

// Add to history
messages = append(messages, Message{Role: "assistant", Content: content1})
messages = append(messages, Message{Role: "user", Content: "Give me an example"})

// Second turn with context
content2, _ := connector.ChatCompletion(ChatCompletionRequest{
    Model:    "gpt-4",
    Messages: messages,
})

fmt.Printf("AI: %s\n", content2)
```

---

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Your App      │         │  Vastar Runtime  │         │  RAI Simulator  │
│  (main.go)      │◄───────►│  (Unix Socket)   │◄───────►│  (HTTP Server)  │
└─────────────────┘   IPC   └──────────────────┘   HTTP  └─────────────────┘
      (Go)                    (FlatBuffers)                  (OpenAI API)
```

### Components

1. **Your Application** - Uses Vastar SDK client
2. **Vastar Runtime** - IPC communication layer (Unix socket/TCP)
3. **RAI Simulator** - Mock OpenAI API server

### Communication Flow

1. App creates request using Vastar SDK
2. SDK sends FlatBuffers message to Runtime via Unix socket
3. Runtime executes HTTP request to Simulator
4. Simulator streams SSE response back
5. Runtime forwards response to App
6. App processes streaming chunks

---

## 📖 API Reference

### OpenAIConnector

```go
type OpenAIConnector struct {
    client  *vastar.RuntimeClient
    baseURL string
}

// Create new connector
func NewOpenAIConnector(baseURL string) (*OpenAIConnector, error)

// Test connection to simulator
func (c *OpenAIConnector) TestConnection() (string, error)

// Streaming chat completion (returns channels)
func (c *OpenAIConnector) ChatCompletionStream(req ChatCompletionRequest) (<-chan string, <-chan error)

// Non-streaming chat completion (returns full text)
func (c *OpenAIConnector) ChatCompletion(req ChatCompletionRequest) (string, error)

// Close connection
func (c *OpenAIConnector) Close() error
```

### Request Types

```go
type ChatCompletionRequest struct {
    Model       string    `json:"model"`
    Messages    []Message `json:"messages"`
    Stream      bool      `json:"stream"`
    MaxTokens   int       `json:"max_tokens,omitempty"`
    Temperature float64   `json:"temperature,omitempty"`
}

type Message struct {
    Role    string `json:"role"`    // "system", "user", "assistant"
    Content string `json:"content"`
}
```

---

## 🔧 Configuration

### Using with Real OpenAI API

To connect to real OpenAI instead of simulator:

**1. Get API Key from [OpenAI Platform](https://platform.openai.com/)**

**2. Set environment variable:**
```bash
export OPENAI_API_KEY="sk-proj-your-api-key-here"
```

**3. Update connector initialization:**
```go
connector, err := NewOpenAIConnectorWithAuth(
    "https://api.openai.com",  // Real OpenAI URL
    os.Getenv("OPENAI_API_KEY"),
)
```

**4. Add Authorization header in requests:**
```go
httpReq := vastar.POST(c.baseURL + "/v1/chat/completions").
    WithHeader("Authorization", "Bearer "+c.apiKey).
    WithHeader("Content-Type", "application/json").
    // ... rest of config
```

See [EXAMPLES.md - Configuration for Real OpenAI API](./EXAMPLES.md#configuration-for-real-openai-api) for complete guide including:
- Authentication setup
- Environment variables
- Configuration file (YAML)
- Supported models (GPT-4, GPT-3.5-turbo)
- Rate limiting handling
- Cost monitoring
- Complete working example

### Simulator URL

Default: `http://localhost:4545`

Change in `main.go`:
```go
connector, err := NewOpenAIConnector("http://localhost:8080") // Custom port
```

### Request Timeout

Default: 5 minutes for streaming

Modify in code:
```go
httpReq := vastar.POST(url).
    WithTimeout(600000) // 10 minutes in milliseconds
```

### Stream Buffer Size

Default: 100 chunks

Adjust in code:
```go
chunkChan := make(chan string, 500) // Larger buffer
```

---

## 🧪 Testing

### Test Connection Only

```bash
go run main.go
# Will show connection test result
```

### Run All Examples

```bash
go run main.go
# Runs 3 complete examples:
# 1. Streaming
# 2. Non-streaming
# 3. Conversation with history
```

### Manual Testing with curl

```bash
# Test simulator directly
curl -X POST http://localhost:4545/test_completion

# Test streaming endpoint
curl -X POST http://localhost:4545/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

See [EXAMPLES.md](./EXAMPLES.md) for more test scenarios.

---

## 🐛 Troubleshooting

### Error: "Failed to connect to runtime"

**Cause:** Vastar Runtime not running

**Solution:**
```bash
# From repository root
cd ../..

# Clean up old instances and start fresh
./clean_vcr.sh
./start_runtime.sh

# Verify it's running
pgrep -a vastar-connector-runtime
ls -la /tmp/vastar-connector-runtime.sock
```

### Error: "Unexpected status code: 400"

**Possible Causes:**

1. **Insufficient Quota:**
   ```json
   "error": {
     "message": "You exceeded your current quota...",
     "type": "insufficient_quota"
   }
   ```
   **Solution:** Add credits to your OpenAI account at https://platform.openai.com/account/billing

2. **Invalid API Key:**
   **Solution:** Check your API key at https://platform.openai.com/api-keys

3. **Invalid Model Name:**
   **Solution:** Use valid model names: `gpt-4`, `gpt-3.5-turbo`, etc.

### Error: "Connection test failed"

**Cause:** RAI Simulator not running or wrong port

**Solution:**
```bash
# Check if simulator is running
curl -X POST http://localhost:4545/test_completion

# If not, start it (Docker)
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

# Or check port mapping
docker ps | grep rai-simulator
```

### Error: "Unexpected status code: 0"

**Cause:** Runtime HTTP implementation placeholder

**Solution:** This is expected if Runtime HTTP is not fully implemented. The example code structure is correct and ready for full HTTP support.

### Streaming Not Working

**Causes:**
1. Stream flag not set to `true`
2. Simulator not supporting SSE
3. Buffer full (chunks not consumed)

**Solution:**
```go
// Ensure stream is enabled
req := ChatCompletionRequest{
    Stream: true, // Must be true
    // ...
}

// Consume chunks immediately
for chunk := range chunks {
    fmt.Print(chunk) // Process immediately
}
```

---

## 📚 Documentation

- **[SETUP.md](./SETUP.md)** - Detailed setup guide for Runtime and Simulator
- **[EXAMPLES.md](./EXAMPLES.md)** - Code examples and test results
- **[../../sdk-golang/README.md](../../sdk-golang/README.md)** - Vastar SDK documentation
- **[../../sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md](../../sdk-golang/CONNECTOR_DEVELOPER_GUIDE.md)** - Connector development guide

---

## 🤝 Contributing

Found a bug or want to improve this example? Contributions welcome!

---

## 📄 License

This example is part of the Vastar Connector SDK project.

**Repository:** https://github.com/fullstack-aidev/vastar-wf-connector-sdk-bin



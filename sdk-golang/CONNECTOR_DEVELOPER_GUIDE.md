# 🚀 Vastar Connector Developer Guide - Go

**Build production-ready connectors with Vastar Go SDK**


---

## 📋 Table of Contents

- [Introduction](#-introduction)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Core Concepts](#-core-concepts)
- [Building Your First Connector](#-building-your-first-connector)
- [Advanced Usage](#-advanced-usage)
- [Best Practices](#-best-practices)
- [Error Handling](#-error-handling)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Introduction

### What is Vastar Connector?

Vastar Connector adalah framework untuk membuat **custom connectors** yang mengintegrasikan aplikasi Anda dengan external APIs, databases, dan services. Framework ini menyediakan:

- ✅ **Connection pooling** - Automatic connection reuse
- ✅ **Circuit breaker** - Prevent cascading failures
- ✅ **Retry logic** - Automatic retry with backoff
- ✅ **Rate limiting** - Prevent API quota exhaustion
- ✅ **Multi-tenancy** - Tenant & workspace isolation
- ✅ **High performance** - FlatBuffers IPC protocol

### Why Use Go SDK?

- ✅ **Native Go support** - Idiomatic Go code
- ✅ **Type safety** - Compile-time error checking
- ✅ **Zero dependencies** - Only FlatBuffers library
- ✅ **High performance** - Sub-millisecond overhead
- ✅ **Production ready** - Tested and verified

---

## 📦 Prerequisites

### 1. Go Installation

```bash
# Check Go version (require 1.21+)
go version

# Should show: go version go1.21.0 or higher
```

### 2. Vastar Runtime Binary

The repository includes runtime binary and helper scripts:

```bash
# Check if runtime exists
ls -lh connector-runtime/vastar-connector-runtime

# Helper scripts available:
# - start_runtime.sh  : Start runtime with auto-cleanup
# - clean_vcr.sh      : Clean up runtime instances
```

**Helper Scripts:**
- `start_runtime.sh` - Automatically cleans up old instances and starts fresh runtime
- `clean_vcr.sh` - Kills all runtime instances and removes socket/log files

### 3. FlatBuffers Compiler (Optional)

Only needed if regenerating schema:
```bash
# Ubuntu/Debian
sudo apt install flatbuffers-compiler

# macOS
brew install flatbuffers

# Verify
flatc --version
```

---

## 💿 Installation

### Method 1: Go Module (Recommended)

```bash
# Initialize your project
mkdir my-connector
cd my-connector
go mod init github.com/myorg/my-connector

# Add Vastar SDK
go get github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang
```

### Method 2: Local Development

```bash
# Clone SDK repository
git clone https://github.com/fullstack-aidev/vastar-wf-connector-sdk-bin.git

# Use in your go.mod
replace github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang => ../vastar-wf-connector-sdk-bin/sdk-golang
```

### Verify Installation

```bash
# Create test file
cat > main.go << 'EOF'
package main

import (
    "fmt"
    vastar "github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang"
)

func main() {
    fmt.Println("Vastar SDK imported successfully!")
    client, err := vastar.NewRuntimeClient()
    if err != nil {
        fmt.Printf("Runtime not running (expected): %v\n", err)
    } else {
        fmt.Println("Connected to runtime!")
        client.Close()
    }
}
EOF

# Run test
go run main.go
```

---

## 🚀 Quick Start

### Step 1: Start Runtime

```bash
# From repository root
cd /path/to/vastar-wf-connector-sdk-bin
./start_runtime.sh

# This will automatically clean up old instances and start fresh
```

### Step 2: Create Your Connector

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

### Step 3: Run Your Connector

```bash
go run main.go
```

**Expected Output:**
```
🐧 Connected via Unix Socket: /tmp/vastar-connector-runtime.sock
Response: Design for failure.
```

---

## 💡 Core Concepts

### 1. Runtime Client

Runtime client adalah koneksi ke Vastar Runtime daemon:

```go
// Default client
client, err := vastar.NewRuntimeClient()

// Custom options
client, err := vastar.NewRuntimeClientWithOptions(
    30*time.Second,  // timeout
    "tenant-123",    // tenant ID
    "workspace-456", // workspace ID
)
```

### 2. HTTP Requests

Semua HTTP requests dibuat dengan builder pattern:

```go
// Simple GET
req := vastar.GET("https://api.example.com/users")

// POST with JSON
req := vastar.POST("https://api.example.com/users").
    WithJSON(map[string]string{
        "name": "John Doe",
        "email": "john@example.com",
    })

// Custom headers
req := vastar.GET("https://api.example.com/protected").
    WithHeader("Authorization", "Bearer token").
    WithHeader("User-Agent", "MyApp/1.0")
```

### 3. Response Handling

Response object berisi semua informasi dari request:

```go
resp, err := client.ExecuteHTTP(req)
if err != nil {
    // Handle error
}

// Access response data
statusCode := resp.StatusCode        // HTTP status code
body := resp.Body                    // Response body ([]byte)
headers := resp.Headers              // Response headers
duration := resp.DurationUs          // Execution time (microseconds)
success := resp.Success              // true if no error
errorMsg := resp.ErrorMessage        // Error message if failed
errorClass := resp.ErrorClass        // Error classification
```

### 4. Error Classification

Semua errors diklasifikasikan untuk memudahkan retry logic:

```go
if err != nil {
    if connErr, ok := err.(*vastar.ConnectorError); ok {
        switch connErr.ErrorClass {
        case ipc.ErrorClassSuccess:
            // No error
        case ipc.ErrorClassTransient:
            // Temporary error - safe to retry immediately
        case ipc.ErrorClassPermanent:
            // Permanent error - don't retry
        case ipc.ErrorClassRateLimited:
            // Rate limited - retry with backoff
        case ipc.ErrorClassTimeout:
            // Timeout - retry with caution
        case ipc.ErrorClassInvalidRequest:
            // Bad request - don't retry
        }
    }
}
```

---

## 🏗️ Building Your First Connector

### Example: GitHub API Connector

```go
package main

import (
    "encoding/json"
    "fmt"
    "log"
    
    vastar "github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang"
)

type GitHubUser struct {
    Login     string `json:"login"`
    Name      string `json:"name"`
    Bio       string `json:"bio"`
    Followers int    `json:"followers"`
}

type GitHubConnector struct {
    client *vastar.RuntimeClient
    token  string
}

func NewGitHubConnector(token string) (*GitHubConnector, error) {
    client, err := vastar.NewRuntimeClient()
    if err != nil {
        return nil, fmt.Errorf("failed to create client: %w", err)
    }
    
    return &GitHubConnector{
        client: client,
        token:  token,
    }, nil
}

func (c *GitHubConnector) Close() error {
    return c.client.Close()
}

func (c *GitHubConnector) GetUser(username string) (*GitHubUser, error) {
    url := fmt.Sprintf("https://api.github.com/users/%s", username)
    
    req := vastar.GET(url).
        WithHeader("Accept", "application/vnd.github.v3+json").
        WithHeader("User-Agent", "Vastar-Connector/1.0")
    
    if c.token != "" {
        req.WithHeader("Authorization", "Bearer "+c.token)
    }
    
    resp, err := c.client.ExecuteHTTP(req)
    if err != nil {
        return nil, fmt.Errorf("request failed: %w", err)
    }
    
    if resp.StatusCode != 200 {
        return nil, fmt.Errorf("unexpected status: %d", resp.StatusCode)
    }
    
    var user GitHubUser
    if err := json.Unmarshal(resp.Body, &user); err != nil {
        return nil, fmt.Errorf("failed to parse response: %w", err)
    }
    
    return &user, nil
}

func main() {
    // Create connector
    connector, err := NewGitHubConnector("")
    if err != nil {
        log.Fatal(err)
    }
    defer connector.Close()
    
    // Get user info
    user, err := connector.GetUser("torvalds")
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("User: %s\n", user.Login)
    fmt.Printf("Name: %s\n", user.Name)
    fmt.Printf("Bio: %s\n", user.Bio)
    fmt.Printf("Followers: %d\n", user.Followers)
}
```

---

## 🎓 Advanced Usage

### 1. Multi-Tenant Support

```go
// Option 1: Set at client level
client, _ := vastar.NewRuntimeClientWithOptions(
    30*time.Second,
    "tenant-acme",      // All requests use this tenant
    "workspace-prod",   // All requests use this workspace
)

// Option 2: Override per request
req := vastar.GET("https://api.example.com/data").
    WithTenantID("tenant-override").
    WithWorkspaceID("workspace-override")
```

### 2. Distributed Tracing

```go
// Add trace ID for correlation
req := vastar.GET("https://api.example.com/data").
    WithTraceID("trace-abc-123-def-456")

// Use with OpenTelemetry or similar
span := tracer.StartSpan("api-call")
req.WithTraceID(span.SpanContext().TraceID().String())
```

### 3. Custom Timeout

```go
// Set timeout per request (in milliseconds)
req := vastar.GET("https://slow-api.example.com/data").
    WithTimeout(60000)  // 60 seconds
```

### 4. Retry Logic

```go
func executeWithRetry(client *vastar.RuntimeClient, req *vastar.HTTPRequest, maxRetries int) (*vastar.HTTPResponse, error) {
    var resp *vastar.HTTPResponse
    var err error
    
    for i := 0; i < maxRetries; i++ {
        resp, err = client.ExecuteHTTP(req)
        
        // Success
        if err == nil {
            return resp, nil
        }
        
        // Check if retryable
        if connErr, ok := err.(*vastar.ConnectorError); ok {
            if !connErr.IsRetryable() {
                return nil, err  // Don't retry permanent errors
            }
            
            // Exponential backoff
            backoff := time.Duration(i+1) * time.Second
            if connErr.ErrorClass == ipc.ErrorClassRateLimited {
                backoff *= 2  // Longer backoff for rate limits
            }
            
            time.Sleep(backoff)
        } else {
            return nil, err
        }
    }
    
    return nil, fmt.Errorf("max retries exceeded: %w", err)
}
```

### 5. Connection Pooling

Connection pooling dihandle otomatis oleh runtime. Anda hanya perlu reuse client:

```go
// Good: Reuse client
client, _ := vastar.NewRuntimeClient()
defer client.Close()

for i := 0; i < 100; i++ {
    req := vastar.GET(fmt.Sprintf("https://api.example.com/users/%d", i))
    resp, _ := client.ExecuteHTTP(req)
    // Process response
}

// Bad: Create new client per request (DON'T DO THIS)
for i := 0; i < 100; i++ {
    client, _ := vastar.NewRuntimeClient()  // ❌ Inefficient!
    req := vastar.GET(fmt.Sprintf("https://api.example.com/users/%d", i))
    resp, _ := client.ExecuteHTTP(req)
    client.Close()
}
```

---

## ✅ Best Practices

### 1. Client Lifecycle

```go
// ✅ Good: Create once, use many times
func main() {
    client, err := vastar.NewRuntimeClient()
    if err != nil {
        log.Fatal(err)
    }
    defer client.Close()  // Always close when done
    
    // Use client for multiple requests
    for _, url := range urls {
        resp, _ := client.ExecuteHTTP(vastar.GET(url))
        // Process response
    }
}

// ❌ Bad: Create/close per request
func badExample() {
    for _, url := range urls {
        client, _ := vastar.NewRuntimeClient()  // ❌ Wasteful!
        resp, _ := client.ExecuteHTTP(vastar.GET(url))
        client.Close()
    }
}
```

### 2. Error Handling

```go
// ✅ Good: Handle all error types
resp, err := client.ExecuteHTTP(req)
if err != nil {
    if connErr, ok := err.(*vastar.ConnectorError); ok {
        log.Printf("Connector error: %s (class: %s, retryable: %v)",
            connErr.Message,
            connErr.ErrorClass,
            connErr.IsRetryable())
    } else {
        log.Printf("Unexpected error: %v", err)
    }
    return err
}

// Check HTTP status
if resp.StatusCode >= 400 {
    log.Printf("HTTP error: %d - %s", resp.StatusCode, resp.Body)
}
```

### 3. Context Propagation

```go
import "context"

func makeRequestWithContext(ctx context.Context, client *vastar.RuntimeClient, url string) error {
    // Check context before making request
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }
    
    req := vastar.GET(url)
    
    // Add trace ID from context
    if traceID := ctx.Value("trace-id"); traceID != nil {
        req.WithTraceID(traceID.(string))
    }
    
    resp, err := client.ExecuteHTTP(req)
    // Handle response
    return err
}
```

### 4. Structured Logging

```go
import "log/slog"

func logRequest(req *vastar.HTTPRequest, resp *vastar.HTTPResponse, err error) {
    if err != nil {
        slog.Error("request failed",
            "url", req.URL,
            "method", req.Method,
            "error", err,
        )
    } else {
        slog.Info("request succeeded",
            "url", req.URL,
            "method", req.Method,
            "status", resp.StatusCode,
            "duration_ms", float64(resp.DurationUs)/1000.0,
        )
    }
}
```

---

## 🧪 Testing

### Unit Testing

```go
package myconnector_test

import (
    "testing"
    
    vastar "github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang"
)

func TestConnectorCreation(t *testing.T) {
    client, err := vastar.NewRuntimeClient()
    if err != nil {
        t.Skip("Runtime not available, skipping")
    }
    defer client.Close()
    
    if client == nil {
        t.Fatal("Expected non-nil client")
    }
}

func TestRequestBuilder(t *testing.T) {
    req := vastar.GET("https://api.example.com/test").
        WithHeader("X-Test", "value").
        WithTimeout(5000)
    
    if req.Method != "GET" {
        t.Errorf("Expected GET, got %s", req.Method)
    }
    
    if req.Headers["X-Test"] != "value" {
        t.Error("Expected X-Test header")
    }
}
```

### Integration Testing

```bash
# Start runtime first
./start_runtime.sh

# Run tests
go test -v ./...
```

---

## 🚢 Deployment

### 1. Binary Deployment

```bash
# Build your connector
go build -o my-connector main.go

# Deploy binary + runtime
scp my-connector user@server:/opt/connectors/
scp ../connector-runtime/vastar-connector-runtime user@server:/opt/connectors/
```

### 2. Systemd Service

```ini
# /etc/systemd/system/vastar-runtime.service
[Unit]
Description=Vastar Connector Runtime
After=network.target

[Service]
Type=simple
User=vastar
ExecStart=/opt/connectors/vastar-connector-runtime
Restart=always

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/my-connector.service
[Unit]
Description=My Custom Connector
After=vastar-runtime.service
Requires=vastar-runtime.service

[Service]
Type=simple
User=vastar
ExecStart=/opt/connectors/my-connector
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. Docker Deployment

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY . .
RUN go build -o connector main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates

WORKDIR /root/
COPY --from=builder /app/connector .
COPY vastar-connector-runtime .

CMD ["./connector"]
```

---

## 🐛 Troubleshooting

### Issue: "Failed to connect to runtime"

**Error:**
```
failed to connect to runtime: dial unix /tmp/vastar-connector-runtime.sock: connect: connection refused
```

**Solution:**
```bash
# Clean up any old instances
./clean_vcr.sh

# Start fresh runtime
./start_runtime.sh

# Check logs if it fails
tail -f /tmp/vastar-runtime.log
```

### Issue: "Timeout waiting for response"

**Solution:**
```go
// Increase timeout
client, _ := vastar.NewRuntimeClientWithOptions(
    120*time.Second,  // 2 minutes
    "default",
    "",
)
```

### Issue: "Module not found"

**Error:**
```
go: module github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang: no matching versions
```

**Solution:**
```bash
# Use replace directive in go.mod
replace github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang => /path/to/sdk
```

---

## 📚 Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VASTAR_SOCKET_PATH` | `/tmp/vastar-connector-runtime.sock` | Unix socket path |
| `VASTAR_TCP_PORT` | `5000` | TCP port |
| `VASTAR_USE_TCP` | `false` | Force TCP mode |

### API Methods

See complete API reference in [`README.md`](./README.md)

### Protocol Specification

See [`../connector-runtime/RUNTIME_INTEGRATION_GUIDE.md`](../connector-runtime/RUNTIME_INTEGRATION_GUIDE.md)

---

## 🎯 Next Steps

1. **Build your connector** using this guide
2. **Test thoroughly** with your target APIs
3. **Deploy to production** using systemd or Docker
4. **Monitor performance** via logs and metrics

---

**Questions or Issues?**

- Read [`README.md`](./README.md) for API reference
- Review examples in [`examples/`](./examples/)



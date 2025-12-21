# Vastar Connector SDK - Go

**Production-ready Go SDK for Vastar Connector Runtime with FlatBuffers IPC**

📚 **[→ Connector Developer Guide](./CONNECTOR_DEVELOPER_GUIDE.md)** - Complete guide for building connectors

> **Note:** This is the Go SDK. We are developing SDKs for 10 additional languages (Python, JavaScript/TypeScript/Node.js, Java, C#, Rust, PHP, Ruby, Kotlin, C/C++, Groovy). All SDKs will use the same FlatBuffers IPC protocol for seamless interoperability.

---

## 🚀 Quick Start

### Prerequisites

1. **Runtime Binary**: `../connector-runtime/vastar-connector-runtime`
2. **Go 1.21+**: `go version`
3. **FlatBuffers Compiler** (for regenerating schema): `flatc --version`

### Installation

```bash
go get github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang
```

### Start Runtime

```bash
./start_runtime.sh
```

### Basic Example

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
        log.Fatal(err)
    }
    defer client.Close()
    
    // Make HTTP request
    req := vastar.GET("https://api.github.com/zen")
    
    resp, err := client.ExecuteHTTP(req)
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("Status: %d\n", resp.StatusCode)
    fmt.Printf("Body: %s\n", resp.Body)
}
```

---

## 📚 API Reference

### Client Creation

#### `NewRuntimeClient() (*RuntimeClient, error)`

Creates a new client with default settings:
- Timeout: 60 seconds
- Tenant: "default"
- Connection: Auto (Unix Socket on Linux/macOS, TCP fallback)

```go
client, err := vastar.NewRuntimeClient()
if err != nil {
    log.Fatal(err)
}
defer client.Close()
```

#### `NewRuntimeClientWithOptions(timeout, tenantID, workspaceID)`

Creates a client with custom settings:

```go
client, err := vastar.NewRuntimeClientWithOptions(
    30*time.Second,   // timeout
    "tenant-123",     // tenant ID
    "workspace-456",  // workspace ID
)
```

### Request Builders

#### HTTP Methods

```go
vastar.GET(url)      // GET request
vastar.POST(url)     // POST request  
vastar.PUT(url)      // PUT request
vastar.DELETE(url)   // DELETE request
```

#### Request Modifiers

```go
req := vastar.GET("https://api.example.com/users").
    WithHeader("Authorization", "Bearer token").
    WithHeader("User-Agent", "MyApp/1.0").
    WithTimeout(5000).                          // milliseconds
    WithTenantID("tenant-123").
    WithWorkspaceID("workspace-456").
    WithTraceID("trace-abc-123")

// POST/PUT with JSON body
req := vastar.POST("https://api.example.com/users").
    WithJSON(map[string]string{
        "name": "John Doe",
        "email": "john@example.com",
    })

// POST/PUT with raw body
req := vastar.POST("https://api.example.com/data").
    WithBody([]byte("raw data")).
    WithHeader("Content-Type", "application/octet-stream")
```

### Execute Request

```go
resp, err := client.ExecuteHTTP(req)
if err != nil {
    // Handle error
    if connErr, ok := err.(*vastar.ConnectorError); ok {
        fmt.Printf("Error class: %s\n", connErr.ErrorClass)
        fmt.Printf("Message: %s\n", connErr.Message)
        fmt.Printf("Retryable: %v\n", connErr.IsRetryable())
    }
    return err
}

// Access response
fmt.Printf("Status: %d\n", resp.StatusCode)
fmt.Printf("Body: %s\n", resp.Body)
fmt.Printf("Duration: %.2fms\n", float64(resp.DurationUs)/1000.0)
```

### Response Structure

```go
type HTTPResponse struct {
    RequestID    uint64                 // Unique request ID
    StatusCode   uint16                 // HTTP status code
    Success      bool                   // true if no error
    Body         []byte                 // Response body
    Headers      map[string]string      // Response headers
    ErrorMessage string                 // Error description (if failed)
    ErrorClass   ipc.ErrorClass         // Error classification
    DurationUs   uint64                 // Execution time (microseconds)
}
```

### Error Handling

```go
resp, err := client.ExecuteHTTP(req)
if err != nil {
    if connErr, ok := err.(*vastar.ConnectorError); ok {
        // Check error class
        switch connErr.ErrorClass {
        case ipc.ErrorClassTransient:
            // Retry immediately
        case ipc.ErrorClassRateLimited:
            // Retry with backoff
        case ipc.ErrorClassTimeout:
            // Retry with caution
        case ipc.ErrorClassPermanent:
            // Don't retry
        }
        
        // Or use helper
        if connErr.IsRetryable() {
            // Safe to retry
        }
    }
}
```

### Error Classes

- `ErrorClassSuccess` - No error
- `ErrorClassTransient` - Temporary error, safe to retry
- `ErrorClassPermanent` - Permanent error, don't retry
- `ErrorClassRateLimited` - Rate limited, retry with backoff
- `ErrorClassTimeout` - Request timeout
- `ErrorClassInvalidRequest` - Bad request, don't retry

---

## 💡 Examples

### Example 1: Simple GET

```go
client, _ := vastar.NewRuntimeClient()
defer client.Close()

req := vastar.GET("https://api.github.com/zen")
resp, err := client.ExecuteHTTP(req)

fmt.Printf("Body: %s\n", resp.Body)
```

### Example 2: POST with JSON

```go
req := vastar.POST("https://jsonplaceholder.typicode.com/posts").
    WithJSON(map[string]string{
        "title": "Test Post",
        "body": "This is a test",
        "userId": "1",
    }).
    WithTimeout(5000)

resp, err := client.ExecuteHTTP(req)
```

### Example 3: Authenticated Request

```go
req := vastar.GET("https://api.stripe.com/v1/charges").
    WithHeader("Authorization", "Bearer sk_test_...").
    WithHeader("Stripe-Version", "2023-10-16")

resp, err := client.ExecuteHTTP(req)
```

### Example 4: Multi-tenant Request

```go
// Option 1: Set at client level
client, _ := vastar.NewRuntimeClientWithOptions(
    30*time.Second,
    "tenant-123",
    "workspace-456",
)

// Option 2: Set per request
req := vastar.GET("https://api.example.com/data").
    WithTenantID("tenant-123").
    WithWorkspaceID("workspace-456")
```

### Example 5: With Distributed Tracing

```go
req := vastar.GET("https://api.example.com/data").
    WithTraceID("trace-abc-123-def-456")  // For correlation

resp, err := client.ExecuteHTTP(req)
```

### Example 6: Error Handling with Retry

```go
var resp *vastar.HTTPResponse
var err error

for i := 0; i < 3; i++ {
    resp, err = client.ExecuteHTTP(req)
    if err == nil {
        break
    }
    
    if connErr, ok := err.(*vastar.ConnectorError); ok {
        if !connErr.IsRetryable() {
            break // Don't retry permanent errors
        }
        
        // Backoff
        time.Sleep(time.Duration(i+1) * time.Second)
    }
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VASTAR_SOCKET_PATH` | `/tmp/vastar-connector-runtime.sock` | Unix socket path |
| `VASTAR_TCP_PORT` | `5000` | TCP port |
| `VASTAR_USE_TCP` | `false` | Force TCP mode |

### Connection Priority

1. **Unix Socket** (Linux/macOS) - Preferred
2. **TCP** (Windows/debugging) - Fallback

```bash
# Force TCP mode
export VASTAR_USE_TCP=true

# Custom socket path
export VASTAR_SOCKET_PATH=/var/run/vastar.sock

# Custom TCP port
export VASTAR_TCP_PORT=6000
```

---

## 🧪 Testing

### Run Examples

```bash
# Start runtime first
./start_runtime.sh

# Run examples
go run examples/simple_get.go
go run examples/simple_post.go
go run examples/test_connection.go
```

### Check Runtime Status

```bash
# Check if running
pgrep -a vastar-connector-runtime

# Check logs
tail -f /tmp/vastar-runtime.log

# Stop runtime
pkill vastar-connector-runtime
```

---

## 🛠️ Development


### Project Structure

```
sdk-golang/
├── client.go                      # Main IPC client
├── go.mod / go.sum                # Dependencies
├── start_runtime.sh               # Start runtime (with auto-cleanup)
├── clean_vcr.sh                   # Clean up runtime instances
├── schemas/
│   └── connector_ipc.fbs          # FlatBuffers schema
└── protocol/
    └── connector_ipc_generated.go # Generated Go code
```

---

## 🐛 Troubleshooting

### "Failed to connect"

**Solution:** Clean up and start fresh runtime
```bash
./clean_vcr.sh      # Clean up old instances
./start_runtime.sh  # Start fresh runtime
```

### Multiple runtime instances

**Solution:** Use cleanup script
```bash
./clean_vcr.sh  # Kills all instances and removes socket
```


### Timeout Errors

**Solution:** Increase timeout
```go
client, _ := vastar.NewRuntimeClientWithOptions(
    120*time.Second,  // 2 minutes
    "default",
    "",
)
```

### Check Runtime Logs

```bash
tail -50 /tmp/vastar-runtime.log
```

---

## 📊 Performance

### Typical Latency

- **IPC overhead**: < 1ms
- **FlatBuffers serialization**: < 1µs
- **Total (local request)**: 2-5ms

### Connection Pooling

Handled automatically by runtime:
- HTTP connections pooled
- Circuit breaker for failing services
- Automatic retry with backoff

---

## 📄 License

Proprietary - Vastar Technologies

---

## 📞 Support

- **Examples**: `examples/`

---

**Status:** ✅ Production Ready


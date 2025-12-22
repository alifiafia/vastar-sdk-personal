# Vastar Connector SDK for TypeScript/Node.js

**Build powerful connectors with TypeScript - Ready to compete with n8n!** 🚀

[![npm version](https://img.shields.io/npm/v/@vastar/connector-sdk.svg)](https://www.npmjs.com/package/@vastar/connector-sdk)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue.svg)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-14+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Note:** This TypeScript SDK is part of the Vastar Connector ecosystem. We're building SDKs for 10+ languages (Go, Java, Python, C#, Rust, PHP, Ruby, C/C++, Groovy, Zig, Swift).

---

## 🌟 Why Choose Vastar TypeScript SDK?

### vs n8n

| Feature | Vastar TS SDK | n8n |
|---------|---------------|-----|
| **Performance** | ⚡ Binary IPC | 🐌 HTTP/JSON |
| **TypeScript** | ✅ Native, Full | ⚠️ Partial |
| **Async/Await** | ✅ Full Support | ✅ Full Support |
| **SSE Streaming** | ✅ Built-in | ⚠️ Limited |
| **Error Handling** | ✅ 6 Classes | ⚠️ Basic |
| **Retry Logic** | ✅ Built-in | ❌ Manual |
| **Connection Pool** | ✅ Runtime | ❌ Manual |
| **Circuit Breaker** | ✅ Runtime | ❌ Manual |
| **Learning Curve** | 🟢 Easy | 🟡 Medium |

---

## 🚀 Quick Start

### Installation

```bash
npm install @vastar/connector-sdk
```

### Basic Usage

```typescript
import { RuntimeClient, HTTPResponseHelper } from '@vastar/connector-sdk';

// Create client
const client = new RuntimeClient({
  tenantId: 'my-tenant',
  timeoutMs: 60000
});

// Connect to runtime
await client.connect();

// Execute HTTP request
const response = await client.executeHTTP({
  method: 'GET',
  url: 'https://api.github.com/zen'
});

// Check response
if (HTTPResponseHelper.is2xx(response)) {
  console.log('Success:', HTTPResponseHelper.getBodyAsString(response));
}

// Cleanup
await client.close();
```

---

## 📚 Features

### ⚡ High Performance

- **Binary Protocol**: FlatBuffers for efficient serialization
- **Unix Socket IPC**: Lower latency than HTTP (Linux/macOS)
- **TCP Fallback**: Works on Windows
- **Connection Pooling**: Automatic via runtime
- **Zero-Copy**: Efficient data handling

### 🎯 Developer Experience

- **Full TypeScript**: Complete type definitions
- **Async/Await**: Modern promise-based API
- **Error Handling**: Comprehensive exception classes
- **Built-in Utilities**: Retry, SSE parser, helpers
- **IntelliSense**: Full IDE support

### 🌊 SSE Streaming

- **Built-in Parser**: OpenAI-compatible
- **Async Generator**: Stream processing
- **Chunk Handling**: Automatic chunking

### 🛡️ Production Ready

- **Error Classification**: 6 error classes
- **Retry Helper**: Exponential backoff
- **Timeout Handling**: Per-request timeouts
- **Circuit Breaker**: Runtime-level protection

---

## 📖 Documentation

- **[TypeScript SDK Guide](docs/TYPESCRIPT_SDK_GUIDE.md)** - Complete developer guide
- **[API Reference](docs/API.md)** - Full API documentation
- **[Examples](examples/)** - Working examples
- **[Runtime Integration](../connector-runtime/RUNTIME_INTEGRATION_GUIDE.md)** - Runtime setup

---

## 💻 Examples

### Simple GET Request

```typescript
import { RuntimeClient, HTTPResponseHelper } from '@vastar/connector-sdk';

const client = new RuntimeClient();
await client.connect();

const response = await client.executeHTTP({
  method: 'GET',
  url: 'https://api.example.com/data',
  headers: {
    'Accept': 'application/json'
  }
});

console.log('Status:', response.statusCode);
console.log('Body:', HTTPResponseHelper.getBodyAsJSON(response));

await client.close();
```

### POST with JSON Body

```typescript
const payload = {
  name: 'John Doe',
  email: 'john@example.com'
};

const response = await client.executeHTTP({
  method: 'POST',
  url: 'https://api.example.com/users',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
});
```

### SSE Streaming (OpenAI)

```typescript
import { SSEParser } from '@vastar/connector-sdk';

const response = await client.executeHTTP({
  method: 'POST',
  url: 'https://api.openai.com/v1/chat/completions',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiKey}`
  },
  body: JSON.stringify({
    model: 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: 'Hello!' }],
    stream: true
  })
});

// Parse SSE stream
const sseData = HTTPResponseHelper.getBodyAsString(response);
const fullResponse = SSEParser.parseStream(sseData);
console.log('AI Response:', fullResponse);
```

### Error Handling with Retry

```typescript
import { RetryHelper, ConnectorException } from '@vastar/connector-sdk';

const result = await RetryHelper.withRetry(
  async () => {
    return await client.executeHTTP({
      method: 'GET',
      url: 'https://api.example.com/unstable'
    });
  },
  {
    maxRetries: 3,
    initialBackoffMs: 1000
  }
);
```

### Using Async/Await Patterns

```typescript
// Parallel requests
const [user, posts, comments] = await Promise.all([
  client.executeHTTP({ method: 'GET', url: '/users/1' }),
  client.executeHTTP({ method: 'GET', url: '/posts' }),
  client.executeHTTP({ method: 'GET', url: '/comments' })
]);

// Sequential requests
const user = await client.executeHTTP({ method: 'GET', url: '/users/1' });
const posts = await client.executeHTTP({ 
  method: 'GET', 
  url: `/users/${user.id}/posts` 
});
```

---

## 🔧 Configuration

### RuntimeClient Options

```typescript
const client = new RuntimeClient({
  tenantId: 'my-tenant',        // Multi-tenancy ID
  workspaceId: 'workspace-123', // Workspace context
  timeoutMs: 60000,             // Default timeout (60s)
  socketPath: '/tmp/custom.sock', // Custom socket path
  useTcp: false,                // Force TCP mode
  tcpHost: '127.0.0.1',        // TCP host
  tcpPort: 5000                 // TCP port
});
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VASTAR_USE_TCP` | Force TCP mode | `false` |
| `VASTAR_SOCKET_PATH` | Unix socket path | `/tmp/vastar-connector-runtime.sock` |
| `VASTAR_TCP_HOST` | TCP host | `127.0.0.1` |
| `VASTAR_TCP_PORT` | TCP port | `5000` |

---

## 🎓 API Reference

### RuntimeClient

#### Constructor

```typescript
new RuntimeClient(config?: RuntimeClientConfig)
```

#### Methods

##### `connect(): Promise<void>`
Connect to Vastar Runtime.

##### `executeHTTP(request: HTTPRequestConfig): Promise<HTTPResponse>`
Execute HTTP request through runtime.

**Parameters:**
- `method`: HTTP method (GET, POST, etc.)
- `url`: Target URL
- `headers?`: Request headers
- `body?`: Request body (string or Buffer)
- `timeoutMs?`: Request timeout
- `tenantId?`: Override tenant ID
- `workspaceId?`: Override workspace ID
- `traceId?`: Distributed tracing ID

**Returns:** `HTTPResponse` object with:
- `requestId`: Request identifier
- `statusCode`: HTTP status code
- `headers`: Response headers
- `body`: Response body (Buffer)
- `durationUs`: Execution duration (microseconds)
- `errorClass`: Error classification
- `errorMessage?`: Error message if failed

##### `close(): Promise<void>`
Close connection to runtime.

### HTTPResponseHelper

Utility methods for working with responses:

- `is2xx(response)`: Check if status is 200-299
- `is3xx(response)`: Check if status is 300-399
- `is4xx(response)`: Check if status is 400-499
- `is5xx(response)`: Check if status is 500-599
- `getBodyAsString(response)`: Get body as string
- `getBodyAsJSON<T>(response)`: Parse body as JSON
- `getHeader(response, name)`: Get header value

### SSEParser

Parse Server-Sent Events streams:

- `parseStream(sseData)`: Parse complete SSE stream
- `parseChunk(sseChunk)`: Parse single SSE chunk
- `parseStreamAsync(sseData)`: Async generator for chunks

### RetryHelper

Execute with automatic retry:

```typescript
RetryHelper.withRetry<T>(
  fn: () => Promise<T>,
  options?: {
    maxRetries?: number;
    initialBackoffMs?: number;
    maxBackoffMs?: number;
    retryableErrors?: string[];
  }
): Promise<T>
```

### ConnectorException

Exception thrown by connector operations:

```typescript
class ConnectorException extends Error {
  requestId: number;
  errorClass: ErrorClass;
  isRetryable(): boolean;
  getErrorClassName(): string;
}
```

### ErrorClass Enum

```typescript
enum ErrorClass {
  Success = 0,
  Transient = 1,      // Retry recommended
  Permanent = 2,      // Do not retry
  RateLimited = 3,    // Wait and retry
  Timeout = 4,        // Operation timeout
  InvalidRequest = 5  // Bad request
}
```

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────┐
│        Your TypeScript/Node.js Application         │
│                                                     │
│  ┌──────────────────────────────────────────────┐ │
│  │  @vastar/connector-sdk                       │ │
│  │  ├─ RuntimeClient (IPC)                      │ │
│  │  ├─ HTTPResponseHelper                       │ │
│  │  ├─ SSEParser                                │ │
│  │  ├─ RetryHelper                              │ │
│  │  └─ ConnectorException                       │ │
│  └────────────┬─────────────────────────────────┘ │
└───────────────┼───────────────────────────────────┘
                │ FlatBuffers IPC
                │ (Unix Socket / TCP)
                ▼
┌───────────────────────────────────────────────────┐
│     Vastar Connector Runtime (Daemon)             │
│  - HTTP Transport Pack (SSE Streaming)            │
│  - Connection Pooling                             │
│  - Circuit Breaker & Retry                        │
│  - Policy Enforcement                             │
└───────────────────────────────────────────────────┘
```

---

## 🧪 Testing

### Run Tests

```bash
npm test
```

### Test with Simulator

```bash
# Start RAI Simulator
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

# Run tests
npm test
```

---

## 🚀 Building from Source

```bash
# Clone repository
git clone https://github.com/vastar/connector-sdk-typescript.git
cd connector-sdk-typescript

# Install dependencies
npm install

# Build
npm run build

# Run tests
npm test
```

---

## 📦 Publishing

```bash
# Build
npm run build

# Publish to npm
npm publish
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **GitHub**: https://github.com/vastar/connector-sdk-typescript
- **npm**: https://www.npmjs.com/package/@vastar/connector-sdk
- **Documentation**: https://docs.vastar.io/typescript-sdk
- **Issues**: https://github.com/vastar/connector-sdk-typescript/issues

---

## 💬 Support

- 📧 Email: support@vastar.io
- 💬 Discord: https://discord.gg/vastar
- 📖 Documentation: https://docs.vastar.io

---

**Built with ❤️ by the Vastar Team**


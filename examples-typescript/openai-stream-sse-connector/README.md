# 🤖 OpenAI Stream SSE Connector - TypeScript

**Streaming Chat Completions with OpenAI using Vastar TypeScript SDK**

[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue.svg)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-14+-green.svg)](https://nodejs.org/)

---

## 📚 Documentation

- **[TypeScript SDK Usage Guide](TYPESCRIPT_SDK_USAGE.md)** - Complete guide for using Vastar TypeScript SDK ⭐
- **[TypeScript SDK README](../../sdk-typescript/README.md)** - SDK overview and API reference
- **[SDK Source Code](../../sdk-typescript/src/)** - Full SDK implementation

---

## 📋 Overview

This example demonstrates how to build an OpenAI-compatible connector using the **Vastar Connector SDK for TypeScript**. It showcases:

- ✅ **Streaming Chat Completions** - SSE (Server-Sent Events) support
- ✅ **Non-Streaming Mode** - Standard HTTP requests
- ✅ **RAI Simulator Support** - Test without OpenAI API key
- ✅ **Real OpenAI API** - Production-ready integration
- ✅ **TypeScript** - Full type safety
- ✅ **Async/Await** - Modern promise-based API
- ✅ **Error Handling** - Comprehensive error management

---

## 🚀 Quick Start

### Prerequisites

1. **Node.js 14+** - [Download](https://nodejs.org/)
2. **Vastar Runtime** - Must be running
3. **RAI Simulator** (for testing) or **OpenAI API Key** (for production)

### Step 1: Install Dependencies

```bash
npm install
```

### Step 2: Configure

Copy the example config and set your API key:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml and set OPENAI_API_KEY environment variable
```

### Step 3: Start Vastar Runtime

From repository root:

```bash
cd ../../
./start_runtime.sh
```

### Step 4: Run with Simulator (Recommended for Testing)

```bash
# Start RAI Simulator
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

# Run example
npm run start:simulator
```

### Step 5: Run with Real OpenAI API

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Run example
npm run start:openai
```

---

## 📖 Usage

### Basic Example

```typescript
import { OpenAIStreamConnector } from './src';

const connector = new OpenAIStreamConnector('config.yaml');

// Connect to runtime
await connector.connect();

// Test connection
await connector.testConnection();

// Streaming chat completion
const response = await connector.streamingChatCompletion(
  'Explain quantum computing in simple terms.'
);
console.log('AI Response:', response);

// Non-streaming chat completion
const answer = await connector.chatCompletion('What is TypeScript?');
console.log('Answer:', answer);

// Close connection
await connector.close();
```

### Using Vastar TypeScript SDK Directly

```typescript
import {
  RuntimeClient,
  HTTPResponseHelper,
  SSEParser,
} from '@vastar/connector-sdk';

// Create client
const client = new RuntimeClient({
  tenantId: 'openai-connector',
  timeoutMs: 60000,
});

// Connect
await client.connect();

// Execute HTTP request
const response = await client.executeHTTP({
  method: 'POST',
  url: 'https://api.openai.com/v1/chat/completions',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiKey}`,
  },
  body: JSON.stringify({
    model: 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: 'Hello!' }],
    stream: true,
  }),
});

// Parse SSE stream
if (HTTPResponseHelper.is2xx(response)) {
  const sseData = HTTPResponseHelper.getBodyAsString(response);
  const fullResponse = SSEParser.parseStream(sseData);
  console.log('AI:', fullResponse);
}

// Close
await client.close();
```

---

## 🎯 Features Demonstrated

### 1. Streaming Chat Completion

Uses SSE (Server-Sent Events) to stream responses from OpenAI:

```typescript
const response = await connector.streamingChatCompletion(
  'Explain quantum computing in simple terms.'
);
```

The SDK's `SSEParser` automatically parses the stream:

```typescript
// SSE format: data: {"choices":[{"delta":{"content":"..."}}]}
const fullContent = SSEParser.parseStream(sseData);
```

### 2. Non-Streaming Mode

Standard HTTP request/response:

```typescript
const answer = await connector.chatCompletion('What is the capital of France?');
```

### 3. Error Handling

Comprehensive error handling with `ConnectorException`:

```typescript
try {
  const response = await connector.streamingChatCompletion(message);
} catch (err) {
  if (err instanceof ConnectorException) {
    console.error('Connector Error:', {
      requestId: err.requestId,
      errorClass: err.getErrorClassName(),
      message: err.message,
    });
  }
}
```

### 4. Configuration Management

YAML-based configuration with environment variable support:

```yaml
openai:
  api_key: ${OPENAI_API_KEY}  # Resolved from environment
  base_url: "https://api.openai.com"
  model: "gpt-3.5-turbo"

runtime:
  tenant_id: "openai-connector"
  timeout_ms: 60000

simulator:
  enabled: false
  base_url: "http://localhost:4545"
```

### 5. Dual Mode (Simulator/Real API)

Switch between simulator and real API:

```bash
# Use simulator
npm run start:simulator

# Use real OpenAI API
npm run start:openai
```

Or via environment variable:

```bash
USE_SIMULATOR=true npm start
USE_SIMULATOR=false npm start
```

---

## 📦 Project Structure

```
openai-stream-sse-connector/
├── src/
│   └── index.ts              # Main connector implementation
├── config.yaml               # Configuration file
├── config.example.yaml       # Example configuration
├── package.json              # npm package config
├── tsconfig.json             # TypeScript config
└── README.md                 # This file
```

---

## 🔧 Configuration

### config.yaml

```yaml
# OpenAI API Configuration
openai:
  api_key: ${OPENAI_API_KEY}    # Set via environment variable
  base_url: "https://api.openai.com"
  model: "gpt-3.5-turbo"
  timeout_ms: 60000

# Vastar Runtime Configuration
runtime:
  tenant_id: "openai-connector"
  workspace_id: "default"
  timeout_ms: 60000

# Simulator Configuration (for testing)
simulator:
  enabled: false                 # true = use simulator, false = use real API
  base_url: "http://localhost:4545"
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `USE_SIMULATOR` | Override simulator mode | `true` or `false` |

---

## 🧪 Testing

### Test with RAI Simulator

```bash
# 1. Start simulator
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

# 2. Verify simulator is running
curl -X POST http://localhost:4545/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"test"}],"stream":false}'

# 3. Run example
npm run start:simulator
```

### Test with Real OpenAI API

```bash
# 1. Set API key
export OPENAI_API_KEY="sk-..."

# 2. Run example
npm run start:openai
```

---

## 📊 Example Output

```
🤖 OpenAI Stream SSE Connector Demo
═════════════════════════════════════════════════════

🧪 Using RAI Simulator
🔗 Base URL: http://localhost:4545

📡 Testing connection...
   URL: http://localhost:4545/v1/chat/completions
✅ Connection successful!

Example 1: Streaming Chat Completion
─────────────────────────────────────────────────────────────
User: Explain quantum computing in simple terms.
AI: 
Quantum computing is a type of computing that uses quantum 
mechanics to process information. Unlike classical computers...
─────────────────────────────────────────────────────────────
📊 Total response length: 1820 characters

Example 2: Non-Streaming Chat Completion
─────────────────────────────────────────────────────────────
User: What is the capital of France?
AI: 
The capital of France is Paris.

Example 3: Sequential Requests
─────────────────────────────────────────────────────────────
Q: What is TypeScript?
A: TypeScript is a statically typed superset of JavaScript...

Q: What is Node.js?
A: Node.js is a JavaScript runtime built on Chrome's V8...

Q: What is async/await?
A: Async/await is a modern way to handle asynchronous...

═════════════════════════════════════════════════════
✅ All examples completed successfully!
```

---

## 🛠️ Development

### Build

```bash
npm run build
```

### Run in Development Mode

```bash
npm run dev
```

### Clean Build

```bash
npm run clean
npm run build
```

---

## 📚 SDK Documentation

For more information about the Vastar TypeScript SDK:

- **[TypeScript SDK README](../../sdk-typescript/README.md)** - SDK overview and API reference
- **[SDK Source Code](../../sdk-typescript/src/)** - Full SDK implementation
- **[Runtime Integration Guide](../../connector-runtime/RUNTIME_INTEGRATION_GUIDE.md)** - Runtime setup

---

## 🎓 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────┐
│   OpenAI Stream Connector (TypeScript)              │
│   - Configuration management                        │
│   - API key handling                                │
│   - Request building                                │
│   - Response parsing                                │
└──────────────────┬──────────────────────────────────┘
                   │ Uses
                   ▼
┌─────────────────────────────────────────────────────┐
│   Vastar TypeScript SDK                             │
│   - RuntimeClient (IPC)                             │
│   - HTTPResponseHelper                              │
│   - SSEParser                                       │
│   - ConnectorException                              │
└──────────────────┬──────────────────────────────────┘
                   │ IPC (FlatBuffers)
                   ▼
┌─────────────────────────────────────────────────────┐
│   Vastar Connector Runtime (Daemon)                 │
│   - HTTP Transport Pack (SSE Streaming)             │
│   - Connection Pooling                              │
│   - Circuit Breaker & Retry                         │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS
                   ▼
┌─────────────────────────────────────────────────────┐
│   OpenAI API / RAI Simulator                        │
│   - Chat Completions                                │
│   - SSE Streaming                                   │
└─────────────────────────────────────────────────────┘
```

### Request Flow

1. **Connector** builds request payload
2. **SDK RuntimeClient** serializes request using FlatBuffers
3. **SDK** sends request to **Runtime** via Unix Socket IPC
4. **Runtime** executes HTTP request to OpenAI API
5. **Runtime** streams SSE response
6. **SDK** parses SSE stream
7. **Connector** processes final result

---

## 🐛 Troubleshooting

### Error: Connection refused

**Cause**: Runtime not running

**Solution**:
```bash
cd ../../
./start_runtime.sh
pgrep vastar-connector-runtime
```

### Error: API key not set

**Cause**: `OPENAI_API_KEY` environment variable not set

**Solution**:
```bash
export OPENAI_API_KEY="sk-..."
```

### Error: Simulator not responding

**Cause**: RAI Simulator not running

**Solution**:
```bash
docker ps | grep rai-simulator
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest
```

### TypeScript Compilation Errors

**Solution**:
```bash
npm install
npm run clean
npm run build
```

---

## 🤝 Contributing

This example is part of the Vastar Connector SDK project. Contributions are welcome!

---

## 📄 License

MIT License - see [LICENSE](../../LICENSE) file for details.

---

## 🔗 Links

- **Vastar SDK**: [sdk-typescript/](../../sdk-typescript/)
- **Runtime Guide**: [connector-runtime/](../../connector-runtime/)
- **Other Examples**: [examples-golang/](../../examples-golang/), [examples-java/](../../examples-java/)

---

**Built with ❤️ using Vastar TypeScript SDK**


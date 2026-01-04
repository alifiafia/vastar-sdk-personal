# Using Vastar Connector TypeScript SDK

**Complete Guide for Building Connectors with TypeScript/Node.js**

This guide explains how to use the Vastar Connector TypeScript SDK to build custom connectors, using the OpenAI Stream SSE Connector as a practical example.

---

## 📚 Table of Contents

1. [SDK Overview](#sdk-overview)
2. [Setup & Installation](#setup--installation)
3. [Basic Usage](#basic-usage)
4. [Building HTTP Requests](#building-http-requests)
5. [Processing Responses](#processing-responses)
6. [SSE Stream Handling](#sse-stream-handling)
7. [Error Handling](#error-handling)
8. [Configuration Management](#configuration-management)
9. [Complete Example Walkthrough](#complete-example-walkthrough)
10. [Best Practices](#best-practices)
11. [TypeScript Tips](#typescript-tips)

---

## SDK Overview

### What is Vastar Connector TypeScript SDK?

The Vastar Connector SDK for TypeScript/Node.js is a powerful library that enables you to build connectors that communicate with external APIs through the Vastar Connector Runtime. The SDK provides:

- **IPC Communication** - FlatBuffers-based protocol over Unix Socket (Linux/macOS) or TCP (Windows)
- **HTTP Operations** - Type-safe HTTP request/response handling
- **SSE Streaming** - Built-in Server-Sent Events parser (OpenAI-compatible)
- **Error Handling** - Comprehensive exception handling with error classification
- **Type Safety** - Full TypeScript support with IntelliSense

### Architecture

```
┌──────────────────────────────────────────────────────┐
│        Your TypeScript/Node.js Connector             │
│                                                       │
│  ┌─────────────────┐                                 │
│  │  Your Code      │  - Configuration                │
│  │  - index.ts     │  - Business logic               │
│  │  - connector    │  - API integration              │
│  └────────┬────────┘                                 │
│           │ Import & Use                             │
│           ▼                                           │
│  ┌─────────────────────────────────────────────┐    │
│  │  Vastar TypeScript SDK                      │    │
│  │  ├─ RuntimeClient (IPC)                     │    │
│  │  ├─ HTTPResponseHelper                      │    │
│  │  ├─ SSEParser                               │    │
│  │  ├─ RetryHelper                             │    │
│  │  └─ ConnectorException                      │    │
│  └────────┬────────────────────────────────────┘    │
└───────────┼──────────────────────────────────────────┘
            │ FlatBuffers IPC
            │ (Unix Socket / TCP)
            ▼
┌───────────────────────────────────────────────────────┐
│     Vastar Connector Runtime (Daemon)                 │
│  - HTTP Transport Pack (SSE Streaming)                │
│  - Connection Pooling                                 │
│  - Circuit Breaker & Retry                            │
└───────────────────────────────────────────────────────┘
```

---

## Setup & Installation

### Prerequisites

- **Node.js 14+** - [Download](https://nodejs.org/)
- **TypeScript 5.3+** - Included in devDependencies
- **Vastar Runtime** - Must be running (see [Runtime Setup](#runtime-setup))

### Step 1: Create Your Project

```bash
mkdir my-connector
cd my-connector
npm init -y
```

### Step 2: Install Dependencies

```bash
# Install TypeScript SDK (from local build or npm)
npm install @vastar/connector-sdk

# Install TypeScript and required types
npm install --save-dev typescript @types/node ts-node

# Optional: YAML config support
npm install yaml
```

### Step 3: Setup TypeScript Configuration

Create `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node"
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

### Step 4: Setup Build Scripts

Update `package.json`:

```json
{
  "scripts": {
    "build": "tsc",
    "start": "npm run build && node dist/index.js",
    "dev": "ts-node src/index.ts",
    "clean": "rm -rf dist"
  }
}
```

### Runtime Setup

Start the Vastar Runtime daemon:

```bash
# From repository root
./start_runtime.sh

# Verify it's running
pgrep vastar-connector-runtime
ls -la /tmp/vastar-connector-runtime.sock
```

---

## Basic Usage

### Creating Your First Connector

Create `src/index.ts`:

```typescript
import {
  RuntimeClient,
  HTTPResponseHelper,
  ConnectorException,
} from '@vastar/connector-sdk';

async function main() {
  // Create runtime client
  const client = new RuntimeClient({
    tenantId: 'my-connector',
    timeoutMs: 60000,
  });

  try {
    // Connect to runtime
    await client.connect();
    console.log('✅ Connected to Vastar Runtime');

    // Make HTTP request
    const response = await client.executeHTTP({
      method: 'GET',
      url: 'https://api.github.com/zen',
      headers: {
        'Accept': 'application/json',
      },
    });

    // Process response
    if (HTTPResponseHelper.is2xx(response)) {
      const body = HTTPResponseHelper.getBodyAsString(response);
      console.log('Success:', body);
    } else {
      console.error('Error:', response.statusCode);
    }

  } catch (error) {
    if (error instanceof ConnectorException) {
      console.error('Connector Error:', {
        requestId: error.requestId,
        errorClass: error.getErrorClassName(),
        message: error.message,
      });
    } else {
      console.error('Error:', error);
    }
  } finally {
    // Cleanup
    await client.close();
  }
}

main().catch(console.error);
```

Run it:

```bash
npm run build
npm start
```

---

## Building HTTP Requests

### RuntimeClient Configuration

```typescript
import { RuntimeClient } from '@vastar/connector-sdk';

// Option 1: Simple configuration
const client = new RuntimeClient({
  tenantId: 'my-connector',
});

// Option 2: Full configuration
const client = new RuntimeClient({
  tenantId: 'production-connector',
  workspaceId: 'workspace-123',
  timeoutMs: 120000,          // 2 minutes default timeout
  socketPath: '/tmp/custom.sock',  // Custom socket path (optional)
  useTcp: false,              // Force TCP mode (optional)
  tcpHost: '127.0.0.1',      // TCP host (optional)
  tcpPort: 5000,              // TCP port (optional)
});

// Connect to runtime
await client.connect();
```

### Making HTTP Requests

#### Simple GET Request

```typescript
const response = await client.executeHTTP({
  method: 'GET',
  url: 'https://api.example.com/users',
  headers: {
    'Accept': 'application/json',
  },
});
```

#### POST Request with JSON Body

```typescript
const payload = {
  username: 'john_doe',
  email: 'john@example.com',
};

const response = await client.executeHTTP({
  method: 'POST',
  url: 'https://api.example.com/users',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer token123',
  },
  body: JSON.stringify(payload),
});
```

#### Request with Custom Timeout

```typescript
const response = await client.executeHTTP({
  method: 'POST',
  url: 'https://api.example.com/slow-operation',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data),
  timeoutMs: 300000,  // 5 minutes for this specific request
});
```

#### PUT/PATCH/DELETE Requests

```typescript
// PUT request
const updateResponse = await client.executeHTTP({
  method: 'PUT',
  url: 'https://api.example.com/users/123',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(updatedData),
});

// DELETE request
const deleteResponse = await client.executeHTTP({
  method: 'DELETE',
  url: 'https://api.example.com/users/123',
  headers: {
    'Authorization': 'Bearer token123',
  },
});
```

---

## Processing Responses

### HTTPResponse Object

```typescript
import { HTTPResponseHelper } from '@vastar/connector-sdk';

const response = await client.executeHTTP({...});

// Access response properties
console.log('Request ID:', response.requestId);
console.log('Status Code:', response.statusCode);
console.log('Headers:', response.headers);
console.log('Body (Buffer):', response.body);
console.log('Duration (μs):', response.durationUs);
```

### HTTPResponseHelper Utilities

```typescript
// Check status code ranges
if (HTTPResponseHelper.is2xx(response)) {
  console.log('Success!');
}

if (HTTPResponseHelper.is4xx(response)) {
  console.log('Client error');
}

if (HTTPResponseHelper.is5xx(response)) {
  console.log('Server error');
}

// Get body as string
const bodyStr = HTTPResponseHelper.getBodyAsString(response);

// Get body as JSON (parsed)
interface User {
  id: number;
  name: string;
  email: string;
}

const user = HTTPResponseHelper.getBodyAsJSON<User>(response);
console.log('User:', user.name);

// Get specific header (case-insensitive)
const contentType = HTTPResponseHelper.getHeader(response, 'Content-Type');
const rateLimitRemaining = HTTPResponseHelper.getHeader(response, 'X-RateLimit-Remaining');
```

### Handling Different Response Types

```typescript
const response = await client.executeHTTP({...});

switch (response.statusCode) {
  case 200:
    // OK
    const data = HTTPResponseHelper.getBodyAsJSON(response);
    console.log('Data:', data);
    break;

  case 201:
    // Created
    console.log('Resource created');
    break;

  case 400:
    // Bad Request
    const error = HTTPResponseHelper.getBodyAsJSON(response);
    console.error('Validation error:', error);
    break;

  case 401:
    // Unauthorized
    console.error('Authentication required');
    break;

  case 404:
    // Not Found
    console.error('Resource not found');
    break;

  case 429:
    // Rate Limited
    const retryAfter = HTTPResponseHelper.getHeader(response, 'Retry-After');
    console.warn(`Rate limited. Retry after: ${retryAfter}s`);
    break;

  case 500:
    // Server Error
    console.error('Server error occurred');
    break;

  default:
    console.log('Unexpected status:', response.statusCode);
}
```

---

## SSE Stream Handling

### Understanding SSE Format

Server-Sent Events (SSE) is a streaming format used by APIs like OpenAI, Anthropic, etc:

```
data: {"id":"123","delta":{"content":"Hello"}}

data: {"id":"123","delta":{"content":" world"}}

data: {"id":"123","delta":{"content":"!"}}

data: [DONE]
```

### Using SSEParser

```typescript
import { SSEParser, HTTPResponseHelper } from '@vastar/connector-sdk';

// Execute request with streaming enabled
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
    stream: true,  // Enable streaming
  }),
});

// Get SSE data
const sseData = HTTPResponseHelper.getBodyAsString(response);

// Parse complete stream
const fullContent = SSEParser.parseStream(sseData);
console.log('Full response:', fullContent);
```

### Parsing Individual SSE Chunks

```typescript
// For manual processing
const chunks = sseData.split('\n\n');

for (const chunk of chunks) {
  if (!chunk.startsWith('data: ')) continue;
  
  const content = SSEParser.parseChunk(chunk);
  if (content) {
    console.log('Chunk:', content);
  }
}
```

### Async Generator for Streaming

```typescript
// Process stream as it arrives (using async generator)
async function processStream(sseData: string) {
  for await (const content of SSEParser.parseStreamAsync(sseData)) {
    process.stdout.write(content);  // Print as it streams
  }
  console.log('\n✅ Stream complete');
}
```

### Custom SSE Parser (Example for Different API)

```typescript
function parseCustomSSE(sseData: string): string {
  const lines = sseData.split('\n');
  let fullContent = '';

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const json = line.substring(6);
      
      if (json.trim() === '[DONE]') break;
      
      try {
        const data = JSON.parse(json);
        // Extract content based on your API structure
        if (data.text) {
          fullContent += data.text;
        }
      } catch (e) {
        // Skip invalid JSON
      }
    }
  }

  return fullContent;
}
```

---

## Error Handling

### Error Types

The SDK provides structured error handling:

```typescript
import { ConnectorException, ErrorClass } from '@vastar/connector-sdk';

try {
  const response = await client.executeHTTP({...});
  
} catch (error) {
  if (error instanceof ConnectorException) {
    // Connector-specific error
    console.error('Request ID:', error.requestId);
    console.error('Error Class:', error.getErrorClassName());
    console.error('Message:', error.message);
    console.error('Retryable:', error.isRetryable());
    
  } else if (error instanceof Error) {
    // Generic error (connection, etc.)
    console.error('Error:', error.message);
  }
}
```

### Error Classes

```typescript
enum ErrorClass {
  Success = 0,        // No error
  Transient = 1,      // Temporary error, retry recommended
  Permanent = 2,      // Permanent error, do not retry
  RateLimited = 3,    // Rate limit exceeded, wait and retry
  Timeout = 4,        // Operation timeout
  InvalidRequest = 5  // Bad request, fix and retry
}
```

### Handling Specific Error Classes

```typescript
import { ErrorClass } from '@vastar/connector-sdk';

try {
  const response = await client.executeHTTP({...});
  
} catch (error) {
  if (error instanceof ConnectorException) {
    switch (error.errorClass) {
      case ErrorClass.Transient:
        // Network hiccup, retry recommended
        console.log('Transient error, will retry...');
        await retryRequest();
        break;

      case ErrorClass.RateLimited:
        // Rate limited, wait before retry
        console.log('Rate limited, waiting...');
        await sleep(5000);
        await retryRequest();
        break;

      case ErrorClass.Timeout:
        // Request took too long
        console.error('Request timeout');
        // Increase timeout or give up
        break;

      case ErrorClass.Permanent:
      case ErrorClass.InvalidRequest:
        // Don't retry these
        console.error('Permanent error:', error.message);
        break;
    }
  }
}
```

### Retry with Exponential Backoff

```typescript
import { RetryHelper } from '@vastar/connector-sdk';

// Automatic retry with exponential backoff
const response = await RetryHelper.withRetry(
  async () => {
    return await client.executeHTTP({
      method: 'GET',
      url: 'https://api.example.com/unstable-endpoint',
    });
  },
  {
    maxRetries: 3,
    initialBackoffMs: 1000,    // Start with 1 second
    maxBackoffMs: 30000,       // Max 30 seconds
    retryableErrors: ['Transient', 'RateLimited', 'Timeout'],
  }
);
```

### Manual Retry Implementation

```typescript
async function executeWithRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  let lastError: Error | null = null;
  let backoffMs = 1000;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
      
    } catch (error) {
      lastError = error as Error;

      // Check if retryable
      if (error instanceof ConnectorException && !error.isRetryable()) {
        throw error;  // Not retryable
      }

      if (attempt === maxRetries) {
        throw error;  // Max retries reached
      }

      // Wait before retry
      console.log(`Retry ${attempt + 1}/${maxRetries} after ${backoffMs}ms`);
      await sleep(backoffMs);
      
      // Exponential backoff
      backoffMs = Math.min(backoffMs * 2, 30000);
    }
  }

  throw lastError;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

---

## Configuration Management

### Using YAML Configuration

Create `config.yaml`:

```yaml
# API Configuration
api:
  base_url: "https://api.example.com"
  api_key: ${API_KEY}  # Resolved from environment variable
  timeout_ms: 60000

# Runtime Configuration
runtime:
  tenant_id: "my-connector"
  workspace_id: "default"
  timeout_ms: 60000

# Feature Flags
features:
  enable_caching: true
  enable_retry: true
  max_retries: 3
```

### Loading Configuration

```typescript
import * as fs from 'fs';
import * as yaml from 'yaml';

interface Config {
  api: {
    base_url: string;
    api_key: string;
    timeout_ms: number;
  };
  runtime: {
    tenant_id: string;
    workspace_id: string;
    timeout_ms: number;
  };
  features: {
    enable_caching: boolean;
    enable_retry: boolean;
    max_retries: number;
  };
}

function loadConfig(path: string): Config {
  const fileContent = fs.readFileSync(path, 'utf-8');
  const config = yaml.parse(fileContent) as Config;

  // Resolve environment variables
  config.api.api_key = resolveEnvVar(config.api.api_key);

  return config;
}

function resolveEnvVar(value: string): string {
  // Replace ${VAR_NAME} with environment variable
  if (value.startsWith('${') && value.endsWith('}')) {
    const envVar = value.substring(2, value.length - 1);
    return process.env[envVar] || '';
  }
  return value;
}

// Usage
const config = loadConfig('config.yaml');
console.log('API Key:', config.api.api_key);
```

### Environment-based Configuration

```typescript
interface Config {
  apiKey: string;
  baseUrl: string;
  environment: 'development' | 'staging' | 'production';
}

function getConfig(): Config {
  const env = process.env.NODE_ENV || 'development';

  const configs = {
    development: {
      apiKey: process.env.DEV_API_KEY || '',
      baseUrl: 'https://dev-api.example.com',
      environment: 'development' as const,
    },
    staging: {
      apiKey: process.env.STAGING_API_KEY || '',
      baseUrl: 'https://staging-api.example.com',
      environment: 'staging' as const,
    },
    production: {
      apiKey: process.env.PROD_API_KEY || '',
      baseUrl: 'https://api.example.com',
      environment: 'production' as const,
    },
  };

  return configs[env] || configs.development;
}
```

---

## Complete Example Walkthrough

Let's build a complete connector step by step.

### Step 1: Project Structure

```
my-openai-connector/
├── src/
│   ├── index.ts           # Main connector
│   ├── config.ts          # Configuration loader
│   └── types.ts           # TypeScript interfaces
├── config.yaml            # Configuration file
├── package.json           # npm config
├── tsconfig.json          # TypeScript config
└── README.md             # Documentation
```

### Step 2: Define Types

`src/types.ts`:

```typescript
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: ChatMessage;
    finish_reason: string;
  }>;
}
```

### Step 3: Configuration Loader

`src/config.ts`:

```typescript
import * as fs from 'fs';
import * as yaml from 'yaml';

export interface AppConfig {
  openai: {
    api_key: string;
    base_url: string;
    model: string;
    timeout_ms: number;
  };
  runtime: {
    tenant_id: string;
    workspace_id: string;
    timeout_ms: number;
  };
}

export function loadConfig(path: string = 'config.yaml'): AppConfig {
  const content = fs.readFileSync(path, 'utf-8');
  const config = yaml.parse(content) as AppConfig;

  // Resolve environment variables
  config.openai.api_key = resolveEnv(config.openai.api_key);

  return config;
}

function resolveEnv(value: string): string {
  if (value.startsWith('${') && value.endsWith('}')) {
    const envVar = value.substring(2, value.length - 1);
    return process.env[envVar] || '';
  }
  return value;
}
```

### Step 4: Main Connector

`src/index.ts`:

```typescript
import {
  RuntimeClient,
  HTTPResponseHelper,
  SSEParser,
  ConnectorException,
} from '@vastar/connector-sdk';
import { loadConfig, AppConfig } from './config';
import { ChatMessage, ChatCompletionRequest } from './types';

class OpenAIConnector {
  private client: RuntimeClient;
  private config: AppConfig;

  constructor(configPath: string = 'config.yaml') {
    this.config = loadConfig(configPath);
    this.client = new RuntimeClient({
      tenantId: this.config.runtime.tenant_id,
      workspaceId: this.config.runtime.workspace_id,
      timeoutMs: this.config.runtime.timeout_ms,
    });
  }

  async connect(): Promise<void> {
    await this.client.connect();
    console.log('✅ Connected to Vastar Runtime');
  }

  async streamingChat(userMessage: string): Promise<string> {
    const payload: ChatCompletionRequest = {
      model: this.config.openai.model,
      messages: [{ role: 'user', content: userMessage }],
      stream: true,
    };

    const response = await this.client.executeHTTP({
      method: 'POST',
      url: `${this.config.openai.base_url}/v1/chat/completions`,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.openai.api_key}`,
      },
      body: JSON.stringify(payload),
      timeoutMs: this.config.openai.timeout_ms,
    });

    if (!HTTPResponseHelper.is2xx(response)) {
      throw new Error(
        `API error: ${response.statusCode} - ${HTTPResponseHelper.getBodyAsString(response)}`
      );
    }

    const sseData = HTTPResponseHelper.getBodyAsString(response);
    return SSEParser.parseStream(sseData);
  }

  async close(): Promise<void> {
    await this.client.close();
  }
}

// Main execution
async function main() {
  const connector = new OpenAIConnector();

  try {
    await connector.connect();

    const response = await connector.streamingChat(
      'Explain TypeScript in simple terms.'
    );

    console.log('AI Response:', response);

  } catch (error) {
    if (error instanceof ConnectorException) {
      console.error('Connector Error:', {
        requestId: error.requestId,
        errorClass: error.getErrorClassName(),
        message: error.message,
      });
    } else {
      console.error('Error:', error);
    }
  } finally {
    await connector.close();
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export { OpenAIConnector };
```

### Step 5: Run the Connector

```bash
# Build
npm run build

# Run
npm start
```

---

## Best Practices

### 1. Always Use Async/Await

```typescript
// ✅ GOOD: Modern async/await
async function fetchData() {
  const response = await client.executeHTTP({...});
  return HTTPResponseHelper.getBodyAsJSON(response);
}

// ❌ BAD: Callback hell
function fetchData(callback) {
  client.executeHTTP({...}).then(response => {
    callback(null, response);
  }).catch(err => {
    callback(err);
  });
}
```

### 2. Implement Proper Error Handling

```typescript
// ✅ GOOD: Comprehensive error handling
try {
  const response = await client.executeHTTP({...});
  
  if (!HTTPResponseHelper.is2xx(response)) {
    throw new Error(`HTTP ${response.statusCode}`);
  }
  
  return HTTPResponseHelper.getBodyAsJSON(response);
  
} catch (error) {
  if (error instanceof ConnectorException) {
    // Handle connector errors
    if (error.isRetryable()) {
      return await retryRequest();
    }
  }
  throw error;
}
```

### 3. Use TypeScript Interfaces

```typescript
// ✅ GOOD: Type-safe
interface User {
  id: number;
  name: string;
  email: string;
}

const user = HTTPResponseHelper.getBodyAsJSON<User>(response);
console.log(user.name);  // Type-safe access

// ❌ BAD: No type safety
const user: any = HTTPResponseHelper.getBodyAsJSON(response);
console.log(user.nmae);  // Typo won't be caught
```

### 4. Reuse RuntimeClient

```typescript
// ✅ GOOD: Reuse client for multiple requests
class MyConnector {
  private client: RuntimeClient;

  constructor() {
    this.client = new RuntimeClient({...});
  }

  async request1() {
    return await this.client.executeHTTP({...});
  }

  async request2() {
    return await this.client.executeHTTP({...});
  }
}

// ❌ BAD: Creating new client per request
async function request1() {
  const client = new RuntimeClient({...});
  return await client.executeHTTP({...});
}
```

### 5. Externalize Configuration

```typescript
// ✅ GOOD: Configuration in file
const config = loadConfig('config.yaml');
const apiKey = config.api.api_key;

// ❌ BAD: Hardcoded values
const apiKey = 'sk-hardcoded123';  // Never!
```

### 6. Use Meaningful Variable Names

```typescript
// ✅ GOOD: Clear intent
const userProfile = await fetchUserProfile(userId);
const isAuthenticated = checkAuthStatus();

// ❌ BAD: Unclear
const x = await fetch(id);
const flag = check();
```

### 7. Handle Cleanup Properly

```typescript
// ✅ GOOD: Proper cleanup
async function run() {
  const client = new RuntimeClient({...});
  try {
    await client.connect();
    // ... operations ...
  } finally {
    await client.close();
  }
}
```

---

## TypeScript Tips

### Type-Safe Configuration

```typescript
interface Config {
  apiUrl: string;
  apiKey: string;
  timeout: number;
}

// Use const assertion for compile-time checking
const config = {
  apiUrl: 'https://api.example.com',
  apiKey: process.env.API_KEY!,
  timeout: 60000,
} as const satisfies Config;
```

### Generic Helper Functions

```typescript
async function fetchAPI<T>(
  client: RuntimeClient,
  url: string
): Promise<T> {
  const response = await client.executeHTTP({
    method: 'GET',
    url,
  });

  if (!HTTPResponseHelper.is2xx(response)) {
    throw new Error(`HTTP ${response.statusCode}`);
  }

  return HTTPResponseHelper.getBodyAsJSON<T>(response);
}

// Usage
interface User {
  id: number;
  name: string;
}

const user = await fetchAPI<User>(client, '/users/1');
console.log(user.name);  // Type-safe!
```

### Union Types for Responses

```typescript
type APIResponse<T> =
  | { success: true; data: T }
  | { success: false; error: string };

async function safeAPICall<T>(
  fn: () => Promise<T>
): Promise<APIResponse<T>> {
  try {
    const data = await fn();
    return { success: true, data };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// Usage
const result = await safeAPICall(() => fetchUser(123));
if (result.success) {
  console.log('User:', result.data);
} else {
  console.error('Error:', result.error);
}
```

---

## Summary

This guide covered:

✅ **SDK Setup** - Installing and configuring TypeScript SDK  
✅ **Basic Usage** - Creating clients and making requests  
✅ **HTTP Operations** - GET, POST, PUT, DELETE with examples  
✅ **Response Processing** - Parsing JSON, checking status codes  
✅ **SSE Streaming** - Handling Server-Sent Events  
✅ **Error Handling** - ConnectorException and retry patterns  
✅ **Configuration** - YAML configs and environment variables  
✅ **Complete Example** - Full OpenAI connector walkthrough  
✅ **Best Practices** - Production-ready patterns  
✅ **TypeScript Tips** - Type-safe code examples

### Next Steps

1. 📖 Read the [TypeScript SDK README](../../sdk-typescript/README.md) for API reference
2. 🔍 Study the [OpenAI example source code](src/index.ts)
3. 💻 Build your own custom connector
4. 🚀 Deploy to production!

### Additional Resources

- **SDK Source**: `../../sdk-typescript/src/`
- **Runtime Guide**: `../../connector-runtime/RUNTIME_INTEGRATION_GUIDE.md`
- **FlatBuffers Protocol**: `../../connector-runtime/FLATBUFFERS_IPC_COMPLETE.md`

---

**For questions or issues**: See the main SDK documentation or contact support.

**Happy Coding!** 🚀


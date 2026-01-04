# Using Vastar Connector Python SDK

**Complete Practical Guide for Building Connectors with Python**

This guide explains how to use the Vastar Connector Python SDK to build custom connectors, using the OpenAI Stream SSE Connector as a practical example.

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
11. [Python Tips](#python-tips)

---

## SDK Overview

### What is Vastar Connector Python SDK?

The Vastar Connector SDK for Python is a powerful library that enables you to build connectors that communicate with external APIs through the Vastar Connector Runtime. The SDK provides:

- **IPC Communication** - FlatBuffers-based protocol over Unix Socket (Linux/macOS) or TCP (Windows)
- **HTTP Operations** - Type-safe HTTP request/response handling with dataclasses
- **SSE Streaming** - Built-in Server-Sent Events parser (OpenAI-compatible)
- **Error Handling** - Comprehensive exception handling with error classification
- **Pythonic API** - snake_case, context managers, type hints

### Architecture

```
┌──────────────────────────────────────────────────────┐
│        Your Python Connector Application             │
│                                                       │
│  ┌─────────────────┐                                 │
│  │  Your Code      │  - Configuration                │
│  │  - main.py      │  - Business logic               │
│  │  - connector    │  - API integration              │
│  └────────┬────────┘                                 │
│           │ Import & Use                             │
│           ▼                                           │
│  ┌─────────────────────────────────────────────┐    │
│  │  vastar_connector_sdk                       │    │
│  │  ├─ RuntimeClient (IPC)                     │    │
│  │  ├─ HTTPResponseHelper                      │    │
│  │  ├─ SSEParser                               │    │
│  │  ├─ retry_with_backoff                      │    │
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

- **Python 3.8+** - [Download](https://www.python.org/)
- **pip** - Python package manager
- **Vastar Runtime** - Must be running (see [Runtime Setup](#runtime-setup))

### Step 1: Create Your Project

```bash
mkdir my-connector
cd my-connector

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Install Vastar SDK (from local or PyPI)
pip install vastar-connector-sdk

# Or from local source
pip install -e /path/to/sdk-python

# Optional: YAML config support
pip install pyyaml
```

### Step 3: Setup Project Structure

```
my-connector/
├── main.py           # Your connector
├── config.yaml       # Configuration
├── requirements.txt  # Dependencies
└── README.md        # Documentation
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

Create `main.py`:

```python
#!/usr/bin/env python3
"""My First Connector"""

from vastar_connector_sdk import (
    RuntimeClient,
    HTTPRequest,
    HTTPResponseHelper,
    ConnectorException,
)

def main():
    # Create runtime client
    client = RuntimeClient()
    
    try:
        # Connect to runtime
        client.connect()
        print("✅ Connected to Vastar Runtime")
        
        # Make HTTP request
        response = client.execute_http(HTTPRequest(
            method="GET",
            url="https://api.github.com/zen",
            headers={"Accept": "text/plain"}
        ))
        
        # Process response
        if HTTPResponseHelper.is_2xx(response):
            body = HTTPResponseHelper.get_body_as_string(response)
            print(f"Success: {body}")
        else:
            print(f"Error: {response.status_code}")
    
    except ConnectorException as e:
        print(f"Connector Error: {e}")
    
    finally:
        # Cleanup
        client.close()

if __name__ == "__main__":
    main()
```

Run it:

```bash
python main.py
```

### Using Context Manager (Recommended)

```python
from vastar_connector_sdk import RuntimeClient, HTTPRequest, HTTPResponseHelper

def main():
    # Context manager automatically handles connect/close
    with RuntimeClient() as client:
        response = client.execute_http(HTTPRequest(
            method="GET",
            url="https://api.example.com/data"
        ))
        
        if HTTPResponseHelper.is_2xx(response):
            print("Success!")

if __name__ == "__main__":
    main()
```

---

## Building HTTP Requests

### RuntimeClient Configuration

```python
from vastar_connector_sdk import RuntimeClient, RuntimeConfig

# Option 1: Simple configuration (uses defaults)
client = RuntimeClient()

# Option 2: Full configuration
config = RuntimeConfig(
    tenant_id="production-connector",
    workspace_id="workspace-123",
    timeout_ms=120000,  # 2 minutes default timeout
    socket_path="/tmp/vastar-connector-runtime.sock",  # Unix socket
    use_tcp=False,      # Use Unix socket (Linux/macOS)
    tcp_host="127.0.0.1",  # TCP host (if use_tcp=True)
    tcp_port=5000,      # TCP port (if use_tcp=True)
)
client = RuntimeClient(config)

# Connect
client.connect()
```

### Making HTTP Requests

#### Simple GET Request

```python
response = client.execute_http(HTTPRequest(
    method="GET",
    url="https://api.example.com/users",
    headers={
        "Accept": "application/json"
    }
))
```

#### POST Request with JSON Body

```python
import json

payload = {
    "username": "john_doe",
    "email": "john@example.com"
}

response = client.execute_http(HTTPRequest(
    method="POST",
    url="https://api.example.com/users",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    },
    body=json.dumps(payload).encode("utf-8")
))
```

#### Request with Custom Timeout

```python
response = client.execute_http(HTTPRequest(
    method="POST",
    url="https://api.example.com/slow-operation",
    headers={"Content-Type": "application/json"},
    body=json.dumps(data).encode("utf-8"),
    timeout_ms=300000  # 5 minutes for this specific request
))
```

#### PUT/PATCH/DELETE Requests

```python
# PUT request
response = client.execute_http(HTTPRequest(
    method="PUT",
    url="https://api.example.com/users/123",
    headers={"Content-Type": "application/json"},
    body=json.dumps(updated_data).encode("utf-8")
))

# DELETE request
response = client.execute_http(HTTPRequest(
    method="DELETE",
    url="https://api.example.com/users/123",
    headers={"Authorization": "Bearer token123"}
))
```

---

## Processing Responses

### HTTPResponse Object

```python
from vastar_connector_sdk import HTTPResponseHelper

response = client.execute_http(HTTPRequest(...))

# Access response properties
print(f"Request ID: {response.request_id}")
print(f"Status Code: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"Body (bytes): {response.body}")
print(f"Duration (μs): {response.duration_us}")
```

### HTTPResponseHelper Utilities

```python
# Check status code ranges
if HTTPResponseHelper.is_2xx(response):
    print("Success!")

if HTTPResponseHelper.is_4xx(response):
    print("Client error")

if HTTPResponseHelper.is_5xx(response):
    print("Server error")

# Get body as string
body_str = HTTPResponseHelper.get_body_as_string(response)

# Get body as JSON (parsed)
data = HTTPResponseHelper.get_body_as_json(response)
print(f"User: {data['name']}")

# Get specific header (case-insensitive)
content_type = HTTPResponseHelper.get_header(response, "Content-Type")
rate_limit = HTTPResponseHelper.get_header(response, "X-RateLimit-Remaining")
```

### Handling Different Response Types

```python
response = client.execute_http(HTTPRequest(...))

if response.status_code == 200:
    # OK
    data = HTTPResponseHelper.get_body_as_json(response)
    print(f"Data: {data}")

elif response.status_code == 201:
    # Created
    print("Resource created")

elif response.status_code == 400:
    # Bad Request
    error = HTTPResponseHelper.get_body_as_json(response)
    print(f"Validation error: {error}")

elif response.status_code == 401:
    # Unauthorized
    print("Authentication required")

elif response.status_code == 404:
    # Not Found
    print("Resource not found")

elif response.status_code == 429:
    # Rate Limited
    retry_after = HTTPResponseHelper.get_header(response, "Retry-After")
    print(f"Rate limited. Retry after: {retry_after}s")

elif response.status_code == 500:
    # Server Error
    print("Server error occurred")

else:
    print(f"Unexpected status: {response.status_code}")
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

```python
from vastar_connector_sdk import SSEParser, HTTPResponseHelper
import json

# Execute request with streaming enabled
response = client.execute_http(HTTPRequest(
    method="POST",
    url="https://api.openai.com/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    },
    body=json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": True  # Enable streaming
    }).encode("utf-8")
))

# Get SSE data
sse_data = HTTPResponseHelper.get_body_as_string(response)

# Parse complete stream
full_content = SSEParser.parse_stream(sse_data)
print(f"Full response: {full_content}")
```

### Processing Stream as Generator

```python
# Get SSE data
sse_data = HTTPResponseHelper.get_body_as_string(response)

# Process chunk by chunk
for content in SSEParser.parse_stream_generator(sse_data):
    print(content, end="", flush=True)

print("\n✅ Stream complete")
```

### Parsing Individual SSE Chunks

```python
# For manual processing
chunks = sse_data.split("\n\n")

for chunk in chunks:
    if not chunk.startswith("data: "):
        continue
    
    content = SSEParser.parse_chunk(chunk)
    if content:
        print(f"Chunk: {content}")
```

---

## Error Handling

### Error Types

The SDK provides structured error handling:

```python
from vastar_connector_sdk import ConnectorException, ErrorClass

try:
    response = client.execute_http(HTTPRequest(...))
    
except ConnectorException as e:
    # Connector-specific error
    print(f"Request ID: {e.request_id}")
    print(f"Error Class: {e.get_error_class_name()}")
    print(f"Message: {e.message}")
    print(f"Retryable: {e.is_retryable()}")

except Exception as e:
    # Generic error (connection, etc.)
    print(f"Error: {e}")
```

### Error Classes

```python
from vastar_connector_sdk import ErrorClass

# Available error classes:
ErrorClass.SUCCESS         # No error
ErrorClass.TRANSIENT       # Temporary error, retry recommended
ErrorClass.PERMANENT       # Permanent error, do not retry
ErrorClass.RATE_LIMITED    # Rate limit exceeded, wait and retry
ErrorClass.TIMEOUT         # Operation timeout
ErrorClass.INVALID_REQUEST # Bad request, fix and retry
```

### Handling Specific Error Classes

```python
from vastar_connector_sdk import ErrorClass, ConnectorException

try:
    response = client.execute_http(HTTPRequest(...))
    
except ConnectorException as e:
    if e.error_class == ErrorClass.TRANSIENT:
        # Network hiccup, retry recommended
        print("Transient error, will retry...")
        # Retry logic here
    
    elif e.error_class == ErrorClass.RATE_LIMITED:
        # Rate limited, wait before retry
        print("Rate limited, waiting...")
        time.sleep(5)
        # Retry logic here
    
    elif e.error_class == ErrorClass.TIMEOUT:
        # Request took too long
        print("Request timeout")
        # Increase timeout or give up
    
    elif e.error_class in (ErrorClass.PERMANENT, ErrorClass.INVALID_REQUEST):
        # Don't retry these
        print(f"Permanent error: {e.message}")
```

### Retry with Exponential Backoff

```python
from vastar_connector_sdk import retry_with_backoff, HTTPRequest

# Automatic retry with exponential backoff
response = retry_with_backoff(
    lambda: client.execute_http(HTTPRequest(
        method="GET",
        url="https://api.example.com/unstable-endpoint"
    )),
    max_retries=3,
    initial_backoff_ms=1000,    # Start with 1 second
    max_backoff_ms=30000,       # Max 30 seconds
    retryable_errors=["TRANSIENT", "RATE_LIMITED", "TIMEOUT"]
)
```

### Manual Retry Implementation

```python
import time

def execute_with_retry(func, max_retries=3):
    """Execute function with retry logic."""
    backoff_ms = 1000
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        
        except ConnectorException as e:
            # Check if retryable
            if not e.is_retryable():
                raise  # Not retryable
            
            if attempt == max_retries:
                raise  # Max retries reached
            
            # Wait before retry
            print(f"Retry {attempt + 1}/{max_retries} after {backoff_ms}ms")
            time.sleep(backoff_ms / 1000.0)
            
            # Exponential backoff
            backoff_ms = min(backoff_ms * 2, 30000)

# Usage
response = execute_with_retry(
    lambda: client.execute_http(HTTPRequest(...))
)
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

```python
import yaml
import os

def load_config(path="config.yaml"):
    """Load configuration from YAML file."""
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Resolve environment variables
    api_key = config["api"]["api_key"]
    if api_key.startswith("${") and api_key.endswith("}"):
        env_var = api_key[2:-1]
        config["api"]["api_key"] = os.environ.get(env_var, "")
    
    return config

# Usage
config = load_config()
print(f"API Key: {config['api']['api_key']}")
```

### Environment-based Configuration

```python
import os

def get_config():
    """Get configuration based on environment."""
    env = os.environ.get("ENV", "development")
    
    configs = {
        "development": {
            "api_key": os.environ.get("DEV_API_KEY", ""),
            "base_url": "https://dev-api.example.com",
            "debug": True
        },
        "staging": {
            "api_key": os.environ.get("STAGING_API_KEY", ""),
            "base_url": "https://staging-api.example.com",
            "debug": True
        },
        "production": {
            "api_key": os.environ.get("PROD_API_KEY", ""),
            "base_url": "https://api.example.com",
            "debug": False
        }
    }
    
    return configs.get(env, configs["development"])
```

---

## Complete Example Walkthrough

Let's build a complete connector step by step.

### Step 1: Project Structure

```
my-openai-connector/
├── main.py           # Main connector
├── config.yaml       # Configuration file
├── requirements.txt  # Dependencies
└── README.md        # Documentation
```

### Step 2: Create Configuration

`config.yaml`:

```yaml
openai:
  api_key: ${OPENAI_API_KEY}
  base_url: "https://api.openai.com"
  model: "gpt-3.5-turbo"
  timeout_ms: 60000

runtime:
  tenant_id: "openai-connector"
  workspace_id: "default"
  timeout_ms: 60000

simulator:
  enabled: false
  base_url: "http://localhost:4545"
```

### Step 3: Create Main Connector

`main.py`:

```python
#!/usr/bin/env python3
"""OpenAI Stream Connector"""

import json
import os
import yaml

from vastar_connector_sdk import (
    RuntimeClient,
    HTTPRequest,
    RuntimeConfig,
    HTTPResponseHelper,
    SSEParser,
    ConnectorException,
)

class OpenAIConnector:
    """OpenAI Stream Connector using Vastar Python SDK."""
    
    def __init__(self, config_path="config.yaml"):
        """Initialize connector with configuration."""
        self.config = self._load_config(config_path)
        
        # Create runtime client
        runtime_config = RuntimeConfig(
            tenant_id=self.config["runtime"]["tenant_id"],
            workspace_id=self.config["runtime"]["workspace_id"],
            timeout_ms=self.config["runtime"]["timeout_ms"]
        )
        self.client = RuntimeClient(runtime_config)
    
    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Resolve environment variables
        api_key = config["openai"]["api_key"]
        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            config["openai"]["api_key"] = os.environ.get(env_var, "")
        
        return config
    
    def _get_base_url(self):
        """Get base URL (simulator or real OpenAI)."""
        if self.config["simulator"]["enabled"]:
            return self.config["simulator"]["base_url"]
        return self.config["openai"]["base_url"]
    
    def chat_completion(self, user_message, stream=False):
        """Send chat completion request."""
        payload = {
            "model": self.config["openai"]["model"],
            "messages": [{"role": "user", "content": user_message}],
            "stream": stream
        }
        
        response = self.client.execute_http(HTTPRequest(
            method="POST",
            url=f"{self._get_base_url()}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config['openai']['api_key']}"
            },
            body=json.dumps(payload).encode("utf-8"),
            timeout_ms=self.config["openai"]["timeout_ms"]
        ))
        
        if not HTTPResponseHelper.is_2xx(response):
            raise Exception(f"API error: {response.status_code}")
        
        body_str = HTTPResponseHelper.get_body_as_string(response)
        
        # Handle SSE or JSON response
        if body_str.startswith("data:"):
            return SSEParser.parse_stream(body_str)
        else:
            data = json.loads(body_str)
            return data["choices"][0]["message"]["content"]

def main():
    """Main function."""
    print("🤖 OpenAI Connector Demo")
    print("=" * 60)
    
    # Create connector
    connector = OpenAIConnector()
    
    try:
        # Connect
        connector.client.connect()
        print("✅ Connected to runtime")
        
        # Test streaming
        print("\n📡 Streaming chat completion...")
        response = connector.chat_completion(
            "Explain Python in simple terms.",
            stream=True
        )
        print(f"AI: {response[:200]}...")
        
    except ConnectorException as e:
        print(f"❌ Error: {e}")
    
    finally:
        connector.client.close()

if __name__ == "__main__":
    main()
```

### Step 4: Create Requirements

`requirements.txt`:

```
vastar-connector-sdk
pyyaml
```

### Step 5: Run the Connector

```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Install dependencies
pip install -r requirements.txt

# Run connector
python main.py
```

---

## Best Practices

### 1. Always Use Context Managers

```python
# ✅ GOOD: Automatic cleanup
with RuntimeClient() as client:
    response = client.execute_http(HTTPRequest(...))

# ❌ BAD: Manual cleanup required
client = RuntimeClient()
client.connect()
response = client.execute_http(HTTPRequest(...))
client.close()  # Easy to forget!
```

### 2. Implement Proper Error Handling

```python
# ✅ GOOD: Comprehensive error handling
try:
    response = client.execute_http(HTTPRequest(...))
    
    if not HTTPResponseHelper.is_2xx(response):
        raise Exception(f"HTTP {response.status_code}")
    
    return HTTPResponseHelper.get_body_as_json(response)

except ConnectorException as e:
    if e.is_retryable():
        return retry_request()
    raise
```

### 3. Use Type Hints

```python
# ✅ GOOD: Type-safe
from vastar_connector_sdk import HTTPResponse
from typing import Dict

def process_response(response: HTTPResponse) -> Dict:
    return HTTPResponseHelper.get_body_as_json(response)

# ❌ BAD: No type safety
def process_response(response):
    return response.body
```

### 4. Use Dataclasses

```python
# ✅ GOOD: Clean configuration
from vastar_connector_sdk import RuntimeConfig

config = RuntimeConfig(
    tenant_id="production",
    timeout_ms=120000
)
client = RuntimeClient(config)
```

### 5. Externalize Configuration

```python
# ✅ GOOD: Configuration in file
config = load_config("config.yaml")
api_key = config["api"]["api_key"]

# ❌ BAD: Hardcoded values
api_key = "sk-hardcoded123"  # Never!
```

### 6. Use Meaningful Variable Names

```python
# ✅ GOOD: Clear intent
user_profile = fetch_user_profile(user_id)
is_authenticated = check_auth_status()

# ❌ BAD: Unclear
x = fetch(id)
flag = check()
```

### 7. Handle Cleanup Properly

```python
# ✅ GOOD: Proper cleanup with context manager
with RuntimeClient() as client:
    # ... operations ...
    pass  # Automatic cleanup

# Or with try/finally
client = RuntimeClient()
try:
    client.connect()
    # ... operations ...
finally:
    client.close()
```

---

## Python Tips

### Type Hints and Annotations

```python
from typing import Optional, Dict, List
from vastar_connector_sdk import HTTPResponse

def fetch_users(
    client: RuntimeClient,
    limit: int = 10
) -> List[Dict]:
    """Fetch users from API."""
    response: HTTPResponse = client.execute_http(...)
    return HTTPResponseHelper.get_body_as_json(response)
```

### Dataclasses for Configuration

```python
from dataclasses import dataclass

@dataclass
class AppConfig:
    api_key: str
    base_url: str
    timeout: int = 60000
    debug: bool = False

config = AppConfig(
    api_key="key123",
    base_url="https://api.example.com"
)
```

### Generator for Processing Streams

```python
def process_sse_stream(sse_data: str):
    """Process SSE stream as generator."""
    for chunk in SSEParser.parse_stream_generator(sse_data):
        # Process each chunk
        yield chunk

# Usage
for content in process_sse_stream(sse_data):
    print(content, end="", flush=True)
```

### Context Manager Protocol

```python
class MyConnector:
    """Custom connector with context manager."""
    
    def __init__(self):
        self.client = RuntimeClient()
    
    def __enter__(self):
        self.client.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        return False

# Usage
with MyConnector() as conn:
    conn.do_something()
```

---

## Summary

This guide covered:

✅ **SDK Setup** - Installing and configuring Python SDK  
✅ **Basic Usage** - Creating clients and making requests  
✅ **HTTP Operations** - GET, POST, PUT, DELETE with examples  
✅ **Response Processing** - Parsing JSON, checking status codes  
✅ **SSE Streaming** - Handling Server-Sent Events  
✅ **Error Handling** - ConnectorException and retry patterns  
✅ **Configuration** - YAML configs and environment variables  
✅ **Complete Example** - Full OpenAI connector walkthrough  
✅ **Best Practices** - Production-ready patterns  
✅ **Python Tips** - Type hints, dataclasses, context managers

### Next Steps

1. 📖 Read the [Python SDK README](../../sdk-python/README.md) for API reference
2. 🔍 Study the [test_openai_simulator.py](test_openai_simulator.py) source code
3. 💻 Build your own custom connector
4. 🚀 Deploy to production!

### Additional Resources

- **SDK Source**: `../../sdk-python/vastar_connector_sdk/`
- **Runtime Guide**: `../../connector-runtime/RUNTIME_INTEGRATION_GUIDE.md`
- **FlatBuffers Protocol**: `../../connector-runtime/FLATBUFFERS_IPC_COMPLETE.md`

---

**For questions or issues**: See the main SDK documentation or contact support.

**Happy Coding with Python!** 🐍🚀


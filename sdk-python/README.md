# Vastar Connector SDK for Python

**Build powerful connectors with Python - Production-ready and easy to use!** 🐍

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Note:** This Python SDK is part of the Vastar Connector ecosystem. We're building SDKs for 10+ languages including Go, Java, TypeScript, Python, C#, Rust, PHP, Ruby, C/C++, Groovy, Zig, and Swift.

---

## 🌟 Why Choose Vastar Python SDK?

### Clean & Pythonic API

```python
from vastar_connector_sdk import RuntimeClient, HTTPRequest

# Context manager support - automatic cleanup
with RuntimeClient() as client:
    response = client.execute_http(HTTPRequest(
        method="GET",
        url="https://api.github.com/zen"
    ))
    print(response.body.decode())
```

### Key Features

- ✅ **Pythonic Design** - snake_case, dataclasses, type hints
- ✅ **High Performance** - Binary FlatBuffers over Unix Socket
- ✅ **Type Safe** - Full type hints for IDE support
- ✅ **Context Managers** - Automatic resource cleanup
- ✅ **SSE Streaming** - Built-in Server-Sent Events parser
- ✅ **Error Handling** - 6 error classes with retry support
- ✅ **Production Ready** - Circuit breaker, connection pooling via runtime
- ✅ **Easy Integration** - Works with Flask, FastAPI, Django

---

## 🚀 Quick Start

### Installation

```bash
# From PyPI (when published)
pip install vastar-connector-sdk

# From source
pip install -e /path/to/sdk-python
```

### Basic Usage

```python
from vastar_connector_sdk import RuntimeClient, HTTPRequest, HTTPResponseHelper

# Create and connect client
client = RuntimeClient()
client.connect()

# Make HTTP request
response = client.execute_http(HTTPRequest(
    method="GET",
    url="https://api.example.com/data",
    headers={"Accept": "application/json"}
))

# Check response
if HTTPResponseHelper.is_2xx(response):
    data = HTTPResponseHelper.get_body_as_json(response)
    print(data)

# Cleanup
client.close()
```

### Using Context Manager (Recommended)

```python
from vastar_connector_sdk import RuntimeClient, HTTPRequest, HTTPResponseHelper

with RuntimeClient() as client:
    response = client.execute_http(HTTPRequest(
        method="POST",
        url="https://api.example.com/users",
        headers={"Content-Type": "application/json"},
        body=b'{"name": "John Doe"}'
    ))
    
    if HTTPResponseHelper.is_2xx(response):
        print("Success!")
```

---

## 📖 Features

### 🎯 Core Features

#### RuntimeClient - IPC Communication

```python
from vastar_connector_sdk import RuntimeClient, RuntimeConfig

# Basic configuration
client = RuntimeClient()

# Advanced configuration
config = RuntimeConfig(
    tenant_id="my-app",
    workspace_id="production",
    timeout_ms=120000,  # 2 minutes
    use_tcp=False,      # Use Unix Socket (Linux/macOS)
)
client = RuntimeClient(config)
```

#### HTTP Operations

```python
from vastar_connector_sdk import HTTPRequest

# GET request
response = client.execute_http(HTTPRequest(
    method="GET",
    url="https://api.example.com/users/1"
))

# POST with JSON
import json
payload = {"username": "john", "email": "john@example.com"}

response = client.execute_http(HTTPRequest(
    method="POST",
    url="https://api.example.com/users",
    headers={"Content-Type": "application/json"},
    body=json.dumps(payload).encode("utf-8")
))

# Custom timeout
response = client.execute_http(HTTPRequest(
    method="GET",
    url="https://api.example.com/slow-endpoint",
    timeout_ms=300000  # 5 minutes
))
```

#### Response Helpers

```python
from vastar_connector_sdk import HTTPResponseHelper

# Status code checks
if HTTPResponseHelper.is_2xx(response):
    print("Success!")

if HTTPResponseHelper.is_4xx(response):
    print("Client error")

if HTTPResponseHelper.is_5xx(response):
    print("Server error")

# Get body as string
body_str = HTTPResponseHelper.get_body_as_string(response)

# Parse JSON
data = HTTPResponseHelper.get_body_as_json(response)

# Get specific header (case-insensitive)
content_type = HTTPResponseHelper.get_header(response, "Content-Type")
rate_limit = HTTPResponseHelper.get_header(response, "X-RateLimit-Remaining")
```

### 🌊 SSE Stream Parsing

```python
from vastar_connector_sdk import SSEParser, HTTPRequest
import json

# Request streaming response
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
        "stream": True
    }).encode("utf-8")
))

# Parse SSE stream
if HTTPResponseHelper.is_2xx(response):
    sse_data = HTTPResponseHelper.get_body_as_string(response)
    full_response = SSEParser.parse_stream(sse_data)
    print(full_response)

# Or use generator for chunk processing
for chunk in SSEParser.parse_stream_generator(sse_data):
    print(chunk, end="", flush=True)
```

### 🚨 Error Handling

```python
from vastar_connector_sdk import ConnectorException, ErrorClass

try:
    response = client.execute_http(HTTPRequest(
        method="GET",
        url="https://api.example.com/data"
    ))
except ConnectorException as e:
    print(f"Request ID: {e.request_id}")
    print(f"Error Class: {e.get_error_class_name()}")
    print(f"Message: {e.message}")
    print(f"Retryable: {e.is_retryable()}")
    
    # Handle specific error classes
    if e.error_class == ErrorClass.RATE_LIMITED:
        print("Rate limited, waiting...")
        time.sleep(5)
    elif e.error_class == ErrorClass.TRANSIENT:
        print("Transient error, retrying...")
```

### 🔄 Retry with Exponential Backoff

```python
from vastar_connector_sdk import retry_with_backoff, HTTPRequest

# Automatic retry
response = retry_with_backoff(
    lambda: client.execute_http(HTTPRequest(
        method="GET",
        url="https://api.example.com/unstable"
    )),
    max_retries=3,
    initial_backoff_ms=1000,
    max_backoff_ms=30000
)
```

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────┐
│        Your Python Application                     │
│                                                     │
│  ┌──────────────────────────────────────────────┐ │
│  │  vastar_connector_sdk                        │ │
│  │  ├─ RuntimeClient (IPC)                      │ │
│  │  ├─ HTTPRequest/HTTPResponse (dataclasses)   │ │
│  │  ├─ HTTPResponseHelper                       │ │
│  │  ├─ SSEParser                                │ │
│  │  ├─ ConnectorException                       │ │
│  │  └─ retry_with_backoff                       │ │
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

## 📦 API Reference

### RuntimeClient

#### `__init__(config: Optional[RuntimeConfig] = None)`

Create RuntimeClient instance.

**Parameters:**
- `config` - Optional RuntimeConfig. If None, uses defaults.

#### `connect() -> None`

Connect to Vastar Runtime.

#### `execute_http(request: HTTPRequest) -> HTTPResponse`

Execute HTTP request through runtime.

**Parameters:**
- `request` - HTTPRequest with method, URL, headers, body

**Returns:**
- HTTPResponse with status, headers, body

**Raises:**
- `ConnectorException` - If request fails

#### `close() -> None`

Close connection to runtime.

#### Context Manager Support

```python
with RuntimeClient() as client:
    # Use client
    pass
# Automatic cleanup
```

### RuntimeConfig

Dataclass for runtime configuration:

```python
@dataclass
class RuntimeConfig:
    tenant_id: str = "default"
    workspace_id: str = ""
    timeout_ms: int = 60000
    socket_path: str = "/tmp/vastar-connector-runtime.sock"
    use_tcp: bool = False
    tcp_host: str = "127.0.0.1"
    tcp_port: int = 5000
```

### HTTPRequest

Dataclass for HTTP requests:

```python
@dataclass
class HTTPRequest:
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    body: Optional[bytes] = None
    timeout_ms: Optional[int] = None
    tenant_id: Optional[str] = None
    workspace_id: Optional[str] = None
    trace_id: Optional[str] = None
```

### HTTPResponse

Dataclass for HTTP responses:

```python
@dataclass
class HTTPResponse:
    request_id: int
    status_code: int
    headers: Dict[str, str]
    body: bytes
    duration_us: int
    error_class: ErrorClass
    error_message: Optional[str] = None
```

### HTTPResponseHelper

Static utility methods:

- `is_2xx(response: HTTPResponse) -> bool`
- `is_3xx(response: HTTPResponse) -> bool`
- `is_4xx(response: HTTPResponse) -> bool`
- `is_5xx(response: HTTPResponse) -> bool`
- `get_body_as_string(response: HTTPResponse, encoding: str = "utf-8") -> str`
- `get_body_as_json(response: HTTPResponse) -> Any`
- `get_header(response: HTTPResponse, name: str) -> Optional[str]`

### SSEParser

Server-Sent Events parser:

- `parse_stream(sse_data: str) -> str` - Parse complete SSE stream
- `parse_chunk(sse_chunk: str) -> Optional[str]` - Parse single chunk
- `parse_stream_generator(sse_data: str) -> Generator[str, None, None]` - Generator for chunks

### ErrorClass

Enum for error classification:

```python
class ErrorClass(IntEnum):
    SUCCESS = 0
    TRANSIENT = 1      # Retry recommended
    PERMANENT = 2      # Do not retry
    RATE_LIMITED = 3   # Wait and retry
    TIMEOUT = 4        # Operation timeout
    INVALID_REQUEST = 5  # Bad request
```

### ConnectorException

Exception with error classification:

```python
class ConnectorException(Exception):
    def __init__(self, message: str, error_class: ErrorClass, request_id: int)
    
    def is_retryable(self) -> bool
    def get_error_class_name(self) -> str
```

### retry_with_backoff

Retry function with exponential backoff:

```python
def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_backoff_ms: int = 1000,
    max_backoff_ms: int = 30000,
    retryable_errors: Optional[List[str]] = None
) -> T
```

---

## 🎓 Complete Examples

### OpenAI Chat Completion

```python
from vastar_connector_sdk import (
    RuntimeClient, HTTPRequest, HTTPResponseHelper, SSEParser
)
import json

with RuntimeClient() as client:
    # Streaming chat completion
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
            "stream": True
        }).encode("utf-8")
    ))
    
    if HTTPResponseHelper.is_2xx(response):
        sse_data = HTTPResponseHelper.get_body_as_string(response)
        full_response = SSEParser.parse_stream(sse_data)
        print(full_response)
```

### REST API Integration

```python
from vastar_connector_sdk import RuntimeClient, HTTPRequest, HTTPResponseHelper
import json

with RuntimeClient() as client:
    # GET users
    response = client.execute_http(HTTPRequest(
        method="GET",
        url="https://api.example.com/users"
    ))
    
    if HTTPResponseHelper.is_2xx(response):
        users = HTTPResponseHelper.get_body_as_json(response)
        for user in users:
            print(user["name"])
    
    # POST new user
    new_user = {"name": "John Doe", "email": "john@example.com"}
    
    response = client.execute_http(HTTPRequest(
        method="POST",
        url="https://api.example.com/users",
        headers={"Content-Type": "application/json"},
        body=json.dumps(new_user).encode("utf-8")
    ))
    
    if HTTPResponseHelper.is_2xx(response):
        created_user = HTTPResponseHelper.get_body_as_json(response)
        print(f"Created user ID: {created_user['id']}")
```

---

## 🧪 Testing

### Run Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=vastar_connector_sdk
```

---

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/vastar/connector-sdk-python.git
cd connector-sdk-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Code Quality

```bash
# Format code
black vastar_connector_sdk/

# Type checking
mypy vastar_connector_sdk/

# Linting
pylint vastar_connector_sdk/
```

---

## 📚 Documentation

- **[Python SDK Usage Guide](../examples-python/openai-stream-sse-connector/PYTHON_SDK_USAGE.md)** - Practical usage guide
- **[OpenAI Example](../examples-python/openai-stream-sse-connector/)** - Working OpenAI connector
- **[Runtime Integration Guide](../connector-runtime/RUNTIME_INTEGRATION_GUIDE.md)** - Runtime setup

---

## 💡 Best Practices

### 1. Always Use Context Managers

```python
# ✅ GOOD: Automatic cleanup
with RuntimeClient() as client:
    response = client.execute_http(...)

# ❌ BAD: Manual cleanup required
client = RuntimeClient()
client.connect()
response = client.execute_http(...)
client.close()  # Easy to forget!
```

### 2. Handle Errors Properly

```python
# ✅ GOOD: Comprehensive error handling
try:
    response = client.execute_http(request)
    if not HTTPResponseHelper.is_2xx(response):
        print(f"HTTP error: {response.status_code}")
except ConnectorException as e:
    if e.is_retryable():
        # Retry logic
        pass
```

### 3. Use Type Hints

```python
# ✅ GOOD: Type-safe
from vastar_connector_sdk import HTTPResponse

def process_response(response: HTTPResponse) -> dict:
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

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **GitHub**: https://github.com/vastar/connector-sdk-python
- **PyPI**: https://pypi.org/project/vastar-connector-sdk/
- **Documentation**: https://docs.vastar.io/python-sdk
- **Issues**: https://github.com/vastar/connector-sdk-python/issues

---

## 💬 Support

- 📧 Email: support@vastar.io
- 💬 Discord: https://discord.gg/vastar
- 📖 Documentation: https://docs.vastar.io

---

**Built with ❤️ using Python**


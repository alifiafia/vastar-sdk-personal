# 🐍 OpenAI Stream SSE Connector - Python

**Streaming Chat Completions with OpenAI using Vastar Python SDK**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Vastar SDK](https://img.shields.io/badge/Vastar%20SDK-Python-green.svg)](../../sdk-python/)

---

## 📚 Documentation

- **[Python SDK Usage Guide](PYTHON_SDK_USAGE.md)** - Complete guide for using Vastar Python SDK ⭐
- **[Python SDK README](../../sdk-python/README.md)** - SDK overview and API reference
- **[SDK Source Code](../../sdk-python/vastar_connector_sdk/)** - Full SDK implementation

---

## 📋 Overview

This example demonstrates how to build an OpenAI-compatible connector using the **Vastar Connector SDK for Python**. It showcases:

- ✅ **Streaming Chat Completions** - SSE (Server-Sent Events) support
- ✅ **Non-Streaming Mode** - Standard HTTP requests
- ✅ **RAI Simulator Support** - Test without OpenAI API key
- ✅ **Real OpenAI API** - Production-ready integration
- ✅ **Python 3.8+** - Modern Python with type hints
- ✅ **Context Managers** - Automatic resource cleanup
- ✅ **Error Handling** - Comprehensive error management

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** - [Download](https://www.python.org/)
2. **Vastar Runtime** - Must be running
3. **RAI Simulator** (for testing) or **OpenAI API Key** (for production)

### Step 1: Start Vastar Runtime

```bash
# From repository root
cd ../../
./start_runtime.sh
```

### Step 2: Install Dependencies

```bash
# Install Python SDK and dependencies
pip install pyyaml

# Note: SDK is imported from local path (../../sdk-python)
```

### Step 3: Run with Simulator

```bash
# Start RAI Simulator (in another terminal)
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

# Run the example
python3 test_openai_simulator.py
```

### Step 4: Run with Real OpenAI API

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Update config.yaml to disable simulator
# Then run
python3 test_openai_simulator.py
```

---

## 📁 Project Structure

```
openai-stream-sse-connector/
├── test_openai_simulator.py  # Complete working example
├── test_simple.py            # Simple test script
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── run_simulator.sh          # Run with simulator
├── run_openai.sh            # Run with real OpenAI
├── PYTHON_SDK_USAGE.md      # SDK usage guide
└── README.md                # This file
```

---

## 💡 Usage Examples

### Basic Example

```python
from vastar_connector_sdk import (
    RuntimeClient,
    HTTPRequest,
    HTTPResponseHelper,
    SSEParser
)
import json

# Create client with context manager
with RuntimeClient() as client:
    # Make request
    response = client.execute_http(HTTPRequest(
        method="POST",
        url="http://localhost:4545/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer dummy-key"
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
```

### Advanced Example with Error Handling

```python
from vastar_connector_sdk import (
    RuntimeClient,
    HTTPRequest,
    RuntimeConfig,
    HTTPResponseHelper,
    ConnectorException,
    ErrorClass
)

# Configure client
config = RuntimeConfig(
    tenant_id="openai-connector",
    timeout_ms=120000
)

with RuntimeClient(config) as client:
    try:
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
                "stream": False
            }).encode("utf-8")
        ))
        
        if HTTPResponseHelper.is_2xx(response):
            data = HTTPResponseHelper.get_body_as_json(response)
            print(data["choices"][0]["message"]["content"])
    
    except ConnectorException as e:
        if e.is_retryable():
            print(f"Retryable error: {e.message}")
        else:
            print(f"Permanent error: {e.message}")
```

---

## 🎯 Features Demonstrated

### 1. Connection Testing

```python
# Test connection to OpenAI or simulator
response = client.execute_http(HTTPRequest(
    method="POST",
    url=f"{base_url}/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    },
    body=json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Test"}],
        "stream": False,
        "max_tokens": 10
    }).encode("utf-8"),
    timeout_ms=10000
))

if HTTPResponseHelper.is_2xx(response):
    print("✅ Connection successful!")
```

### 2. Streaming Chat Completion

```python
# Stream response in real-time
response = client.execute_http(HTTPRequest(
    method="POST",
    url=f"{base_url}/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    },
    body=json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Explain Python"}],
        "stream": True
    }).encode("utf-8")
))

if HTTPResponseHelper.is_2xx(response):
    sse_data = HTTPResponseHelper.get_body_as_string(response)
    full_response = SSEParser.parse_stream(sse_data)
    print(full_response)
```

### 3. Non-Streaming Chat Completion

```python
# Get complete response at once
response = client.execute_http(HTTPRequest(
    method="POST",
    url=f"{base_url}/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    },
    body=json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
        "stream": False
    }).encode("utf-8")
))

if HTTPResponseHelper.is_2xx(response):
    body_str = HTTPResponseHelper.get_body_as_string(response)
    
    # Handle both SSE and JSON formats
    if body_str.startswith("data:"):
        answer = SSEParser.parse_stream(body_str)
    else:
        data = json.loads(body_str)
        answer = data["choices"][0]["message"]["content"]
    
    print(answer)
```

### 4. Sequential Requests

```python
# Make multiple requests in sequence
questions = [
    "What is Python?",
    "What is asyncio?",
    "What is a decorator?"
]

for question in questions:
    response = client.execute_http(HTTPRequest(
        method="POST",
        url=f"{base_url}/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        body=json.dumps({
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": question}],
            "stream": False
        }).encode("utf-8")
    ))
    
    if HTTPResponseHelper.is_2xx(response):
        body_str = HTTPResponseHelper.get_body_as_string(response)
        
        if body_str.startswith("data:"):
            answer = SSEParser.parse_stream(body_str)
        else:
            data = json.loads(body_str)
            answer = data["choices"][0]["message"]["content"]
        
        print(f"Q: {question}")
        print(f"A: {answer[:100]}...")
```

---

## ⚙️ Configuration

### config.yaml

```yaml
# OpenAI API Configuration
openai:
  api_key: ${OPENAI_API_KEY}
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
  enabled: false
  base_url: "http://localhost:4545"
```

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (for production)
- `USE_SIMULATOR` - Set to `true` to use RAI Simulator

---

## 🧪 Testing

### Test with RAI Simulator

```bash
# 1. Start runtime
cd ../../
./start_runtime.sh

# 2. Start simulator
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

# 3. Run test
cd examples-python/openai-stream-sse-connector
python3 test_openai_simulator.py
```

**Expected Output:**

```
🤖 OpenAI Stream Connector Demo - Python
═════════════════════════════════════════════════════════════

🧪 Using RAI Simulator
🔗 Base URL: http://localhost:4545

🐧 Connected via Unix Socket: /tmp/vastar-connector-runtime.sock
📡 Testing connection...
✅ Connection successful! (SSE stream detected)

Example 1: Streaming Chat Completion
─────────────────────────────────────────────────────────────
User: Explain quantum computing in simple terms.
AI: [Full AI response...]
─────────────────────────────────────────────────────────────
📊 Total response length: 2456 characters

Example 2: Non-Streaming Chat Completion
─────────────────────────────────────────────────────────────
User: What is the capital of France?
AI: [Full AI response...]

Example 3: Sequential Requests
─────────────────────────────────────────────────────────────
Q: What is Python?
A: [Response preview...]

Q: What is asyncio?
A: [Response preview...]

Q: What is a decorator?
A: [Response preview...]

═════════════════════════════════════════════════════════════
✅ All examples completed successfully!
```

### Test with Real OpenAI API

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Run test
python3 test_openai_simulator.py
```

---

## 🔧 Development

### Install Development Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e ../../sdk-python
```

### Run Simple Test

```bash
# Test basic SDK functionality
python3 test_simple.py
```

### Code Format

```bash
# Format code with black
black test_openai_simulator.py test_simple.py

# Type checking
mypy test_openai_simulator.py
```

---

## 🐛 Troubleshooting

### Runtime Not Running

**Error:** `Connection refused` or `No such file or directory`

**Solution:**
```bash
# Check if runtime is running
pgrep vastar-connector-runtime

# If not running, start it
cd ../../
./start_runtime.sh

# Verify socket exists
ls -la /tmp/vastar-connector-runtime.sock
```

### Simulator Not Running

**Error:** `Connection refused` on port 4545

**Solution:**
```bash
# Check if simulator is running
docker ps | grep rai-simulator

# If not running, start it
docker run -d --name rai-simulator -p 4545:4545 rai-endpoint-simulator:latest

# Test simulator
curl -X POST http://localhost:4545/test_completion
```

### Import Error

**Error:** `ModuleNotFoundError: No module named 'vastar_connector_sdk'`

**Solution:**
```bash
# Make sure you're in the example directory
cd examples-python/openai-stream-sse-connector

# The script adds SDK to path automatically:
# sys.path.insert(0, '../../sdk-python')
```

### OpenAI API Key Not Set

**Error:** `Empty API key` or `401 Unauthorized`

**Solution:**
```bash
# Set environment variable
export OPENAI_API_KEY="sk-your-key-here"

# Or update config.yaml directly (not recommended)
```

---

## 📊 Example Output

### Successful Run

```
🤖 OpenAI Stream Connector Demo - Python
═════════════════════════════════════════════════════════════

🧪 Using RAI Simulator
🔗 Base URL: http://localhost:4545

🐧 Connected via Unix Socket: /tmp/vastar-connector-runtime.sock
📡 Testing connection...
✅ Connection successful! (SSE stream detected)
   Response preview: data: {"id":"chatcmpl-...","object":"chat.completion.chunk"...

Example 1: Streaming Chat Completion
─────────────────────────────────────────────────────────────
User: Explain quantum computing in simple terms.
AI: 
**Pertanyaan:**

Bagaimana peran teknologi dan kecerdasan buatan (Artificial Intelligence) 
dalam meningkatkan efisiensi birokrasi di Indonesia?

**Jawaban:**

Teknologi dan kecerdasan buatan (Artificial Intelligence/AI) memiliki 
potensi besar untuk meningkatkan efisiensi birokrasi di Indonesia...
[Full response continues...]
─────────────────────────────────────────────────────────────
📊 Total response length: 2456 characters

Example 2: Non-Streaming Chat Completion
─────────────────────────────────────────────────────────────
User: What is the capital of France?
AI: [Response about French capital...]

Example 3: Sequential Requests
─────────────────────────────────────────────────────────────
Q: What is Python?
A: **Tanya:** Apa tantangan utama dalam pengembangan sektor pendidikan...

Q: What is asyncio?
A: **Pertanyaan:** Bagaimana peran birokrasi dalam mendorong adopsi...

Q: What is a decorator?
A: **Pertanyaan:** Bagaimana kebijakan pemerintah Indonesia dalam...

═════════════════════════════════════════════════════════════
✅ All examples completed successfully!
✅ Connection closed
```

---

## 🎓 Learning Resources

### SDK Documentation

- **[PYTHON_SDK_USAGE.md](PYTHON_SDK_USAGE.md)** - Comprehensive SDK usage guide
- **[SDK README](../../sdk-python/README.md)** - API reference and features
- **[Runtime Guide](../../connector-runtime/RUNTIME_INTEGRATION_GUIDE.md)** - Runtime setup

### Code Examples

- **[test_openai_simulator.py](test_openai_simulator.py)** - Complete working example
- **[test_simple.py](test_simple.py)** - Simple test script

---

## 🤝 Contributing

Found a bug or want to improve this example? Contributions are welcome!

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License

This example is part of the Vastar Connector SDK project.

---

## 🔗 Links

- **Python SDK**: [../../sdk-python/](../../sdk-python/)
- **Go SDK**: [../../sdk-golang/](../../sdk-golang/)
- **Java SDK**: [../../sdk-java/](../../sdk-java/)
- **TypeScript SDK**: [../../sdk-typescript/](../../sdk-typescript/)

---

**Built with ❤️ using Python and Vastar Connector SDK** 🐍


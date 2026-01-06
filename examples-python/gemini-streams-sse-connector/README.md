# 🧠 Gemini Stream Connector — Python

**Secure & Observable AI Orchestration using Vastar Runtime**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Vastar Runtime](https://img.shields.io/badge/Vastar-Runtime-green.svg)]()

---

## 📋 Overview

Project ini mendemonstrasikan integrasi **Google Gemini** menggunakan **Vastar Connector SDK for Python**
dengan dukungan:

* ✅ **RAI Simulator** (offline testing, tanpa API key)
* ✅ **Vastar Runtime** (isolasi & orkestrasi aman)
* ✅ **Non-Streaming & Streaming pattern**
* ✅ **Pure Python vs Vastar Load Testing**
* ✅ **Latency & Performance Measurement**

---

## 📁 Project Structure

```
gemini-streams-sse-connector/
├── main.py                   # Gemini Adapter API (FastAPI)
├── test_gemini_simulator.py  # Main demo script
├── test_simple.py            # Minimal connectivity test
├── phase1_test_gemini.py     # Basic runtime validation
├── loadtest/
│   ├── loadtest_pure.py      # Load test tanpa runtime
│   └── loadtest_vastar.py    # Load test melalui Vastar
├── run_simulator.sh          # Helper menjalankan simulator
├── run_gemini.sh             # Helper menjalankan mode real API
├── requirements.txt
├── PYTHON_SDK_USAGE.md
└── README.md
```

---

## 🚀 Quick Start

### 1. Start Vastar Runtime

```bash
cd ../../
./start_runtime.sh
```

Pastikan socket tersedia:
```bash
ls /tmp/vastar-connector-runtime.sock
```

---
### 2. Start Gemini Simulator

```bash
uvicorn gemini_adapter:app --port 4545
```

---
### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---
### 4. Run Main Demo

```bash
python3 test_gemini_simulator.py
```

---

## 💡 Usage Example

### Basic Gemini Request

```python
from vastar_connector_sdk import RuntimeClient, HTTPRequest, HTTPResponseHelper
import json

with RuntimeClient() as client:
    response = client.execute_http(HTTPRequest(
        method="POST",
        url="http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "contents": [{"parts": [{"text": "Explain AI"}]}]
        }).encode()
    ))

    if HTTPResponseHelper.is_2xx(response):
        data = json.loads(HTTPResponseHelper.get_body_as_string(response))
        print(data["candidates"][0]["content"]["parts"][0]["text"])
```

---
## 🧪 Testing

### Run Demo

```bash
python3 test_gemini_simulator.py
```

### Expected Output

```
🤖 Gemini Connector Demo - Python
═════════════════════════════════════════════════════════════

🧪 Using RAI Simulator
🔗 Base URL: http://localhost:4545

📡 Testing connection...
✅ Connection successful!

Example 1: Content Generation
─────────────────────────────────────────────────────────────
User : Explain Runtime Connector in simple terms.
AI   : A Runtime Connector is a secure communication layer between...
─────────────────────────────────────────────────────────────

Example 2: Sequential Requests
─────────────────────────────────────────────────────────────
Q: What is Gemini AI?
A: Gemini AI is a multimodal artificial intelligence system...

Q: What is Server-Sent Events (SSE)?
A: Server-Sent Events is a streaming technology...

═════════════════════════════════════════════════════════════
✅ All Gemini examples completed successfully!
```

---

## 📊 Load Testing

### Pure Python

```bash
cd loadtest
python loadtest_pure.py
```

### Vastar Runtime

```bash
python loadtest_vastar.py
```

Output contoh:

```
📊 HASIL PENGUJIAN
- Total Request
- Success / Error
- Average Latency
- Min / Max
- P50 / P95
```

---

## 🧠 Architecture Summary

```
Workflow / Test Script
        ↓
Vastar Runtime (isolated execution)
        ↓
Gemini Adapter / RAI Simulator
        ↓
Simulated or Real Gemini API
```

Keunggulan arsitektur:

* Tidak ada komunikasi langsung ke sistem eksternal dari workflow
* Fault isolation & error containment
* Observability penuh
* Aman untuk orkestrasi AI skala besar

---

## 🐛 Troubleshooting

### Runtime not running

```bash
pgrep vastar-connector-runtime
```

Jika tidak aktif:

```bash
cd ../../
./start_runtime.sh
```

---

### Simulator not running

```bash
curl http://localhost:4545
```

Jika gagal:

```bash
uvicorn gemini_adapter:app --port 4545
```

---

## 📄 License

This project is part of the **Vastar Connector SDK**.

---

## ❤️ Built with Python & Vastar Runtime

**AI orchestration made safe, scalable, and observable.**

---
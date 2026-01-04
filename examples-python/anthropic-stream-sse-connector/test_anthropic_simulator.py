#!/usr/bin/env python3
"""
Anthropic Claude Stream Connector - Simulator Test
Vastar Connector SDK - Python
"""

import os
import sys
import json
import yaml

# =========================================================
# Import Vastar Python SDK
# =========================================================
sys.path.insert(0, "../../sdk-python")

from vastar_connector_sdk import (
    RuntimeClient,
    RuntimeConfig,
    HTTPRequest,
    HTTPResponseHelper,
    ConnectorException,
)

# =========================================================
# Load config.yaml (WAJIB TIDAK DIUBAH)
# =========================================================
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

ANTHROPIC_CFG = cfg["anthropic"]
RUNTIME_CFG = cfg["runtime"]
SIMULATOR_CFG = cfg["simulator"]

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "dummy-key")
BASE_URL = ANTHROPIC_CFG["base_url"]
MODEL = ANTHROPIC_CFG["model"]
TIMEOUT_MS = ANTHROPIC_CFG["timeout_ms"]

print("\n🧠 Anthropic Claude Stream Connector - Simulator")
print("═" * 55)
print(f"\n🌐 Using {'RAI Simulator' if SIMULATOR_CFG['enabled'] else 'Live API'}")
print(f"🔗 Base URL: {BASE_URL}")

# =========================================================
# Runtime Client
# =========================================================
client = RuntimeClient(
    RuntimeConfig(
        tenant_id=RUNTIME_CFG["tenant_id"],
        workspace_id=RUNTIME_CFG["workspace_id"],
        timeout_ms=RUNTIME_CFG["timeout_ms"],
    )
)
client.connect()
print(f"🐧 Connected via Unix Socket: /tmp/vastar-connector-runtime.sock")

# =========================================================
# Helper: Send Anthropic request via Runtime
# =========================================================
def send_claude_request(prompt: str, max_tokens: int = 256) -> str:
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {"maxOutputTokens": max_tokens}
    }

    # Gunakan simulator jika enabled
    url = SIMULATOR_CFG["base_url"] if SIMULATOR_CFG["enabled"] else f"{BASE_URL}/v1/complete"

    request = HTTPRequest(
        method="POST",
        url=url,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        body=json.dumps(payload).encode("utf-8"),
        timeout_ms=TIMEOUT_MS
    )

    try:
        response = client.execute_http(request)
        body = HTTPResponseHelper.get_body_as_string(response)

        if not HTTPResponseHelper.is_2xx(response):
            raise RuntimeError(f"Anthropic API error {response.status_code}: {body}")

        # Simulator bisa pakai JSON biasa
        try:
            data = json.loads(body)
            if "text" in data:
                return data["text"]
            elif "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                return body
        except json.JSONDecodeError:
            return body

    except ConnectorException as e:
        return f"[SIMULATOR ERROR] {e.message}"

# =========================================================
# Example 0: Connection Test
# =========================================================
print("\n📡 Testing simulator connection...")
test_prompt = "Ping"
resp = send_claude_request(test_prompt)
print(f"✅ Connection successful! Response: {resp}")

# =========================================================
# Example 1: Streaming Chat Completion (Simulator)
# =========================================================
print("\nExample 1: Streaming Chat Completion")
print("─" * 55)
prompt = "Explain quantum computing in simple terms."
print(f"User: {prompt}")
print("AI:")
answer = send_claude_request(prompt, max_tokens=300)
print(answer)

# =========================================================
# Example 2: Non-streaming Question
# =========================================================
print("\nExample 2: Simple Question")
print("─" * 55)
prompt = "What is the capital of France?"
print(f"User: {prompt}")
print("AI:")
answer = send_claude_request(prompt, max_tokens=50)
print(answer)

# =========================================================
# Example 3: Sequential Requests
# =========================================================
print("\nExample 3: Sequential Requests")
print("─" * 55)
questions = [
    "What is Python?",
    "What is asyncio?",
    "What is a decorator?"
]

for q in questions:
    print(f"\nQ: {q}")
    answer = send_claude_request(q, max_tokens=120)
    print(f"A: {answer}")

# =========================================================
# Cleanup
# =========================================================
client.close()
print("\n✅ All simulator examples completed successfully")
print("═" * 55)

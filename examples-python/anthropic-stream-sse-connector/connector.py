#!/usr/bin/env python3
"""
Anthropic Claude Stream SSE Connector - Python
Vastar Connector Runtime Compatible
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
)

# =========================================================
# Banner
# =========================================================
print("\n🧠 Anthropic Claude Stream Connector - Python")
print("═" * 55)

# =========================================================
# Load config.yaml (TIDAK DIUBAH)
# =========================================================
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

ANTHROPIC_CFG = cfg["anthropic"]
RUNTIME_CFG = cfg["runtime"]

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
BASE_URL = ANTHROPIC_CFG["base_url"]
MODEL = ANTHROPIC_CFG["model"]
TIMEOUT_MS = ANTHROPIC_CFG["timeout_ms"]

if not API_KEY:
    raise RuntimeError("❌ ANTHROPIC_API_KEY belum diset")

print(f"🔗 Base URL: {BASE_URL}")
print(f"🤖 Model: {MODEL}")

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

# =========================================================
# Claude SSE Parser
# =========================================================
def parse_claude_sse(body: str) -> str:
    """
    Gabungkan seluruh SSE event Claude jadi 1 teks utuh
    """
    result = []

    for line in body.splitlines():
        line = line.strip()

        if not line.startswith("data:"):
            continue

        data_str = line[len("data:"):].strip()

        if data_str == "[DONE]":
            break

        try:
            payload = json.loads(data_str)
        except json.JSONDecodeError:
            continue

        delta = payload.get("delta", {})
        text = delta.get("text")
        if text:
            result.append(text)

    return "".join(result)

# =========================================================
# Helper: Send Claude Request
# =========================================================
def send_claude_request(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 400,
        "stream": True,
    }

    request = HTTPRequest(
        method="POST",
        url=f"{BASE_URL}/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
        body=json.dumps(payload).encode("utf-8"),
        timeout_ms=TIMEOUT_MS,
    )

    response = client.execute_http(request)

    body = HTTPResponseHelper.get_body_as_string(response)

    if not HTTPResponseHelper.is_2xx(response):
        raise RuntimeError(
            f"Anthropic API error {response.status_code}: {body}"
        )

    return body

# =========================================================
# Example: Streaming Completion
# =========================================================
print("\n📡 Testing Claude Streaming...")

question = "Explain artificial intelligence in simple terms."

raw = send_claude_request(question)
answer = parse_claude_sse(raw)

print("\nUser:", question)
print("\nAI:")
print(answer)

# =========================================================
# Cleanup
# =========================================================
client.close()
print("\n✅ Claude connector finished successfully")
print("═" * 55)

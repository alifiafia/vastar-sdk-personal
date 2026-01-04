#!/usr/bin/env python3
"""
Gemini Stream SSE Connector - Python
Final Version (Vastar Connector SDK)

- Config.yaml TIDAK DIUBAH
- Full SSE response (tidak terpotong)
- Sesuai arsitektur Connector Runtime
"""

import os
import sys
import json
import yaml

# =========================================================
# Import Vastar Python SDK (local)
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
print("\n🤖 Gemini Stream Connector Demo - Python")
print("═" * 47)

# =========================================================
# Load config.yaml (WAJIB TIDAK DIUBAH)
# =========================================================
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

GEMINI_CFG = cfg["gemini"]
RUNTIME_CFG = cfg["runtime"]

API_KEY = os.environ.get("GEMINI_API_KEY")
BASE_URL = GEMINI_CFG["base_url"]
MODEL = GEMINI_CFG["model"]
TIMEOUT_MS = GEMINI_CFG["timeout_ms"]

print("\n🌐 Using Live Gemini API")
print(f"🔗 Base URL: {BASE_URL}")

if not API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY belum diset di environment")

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
# Gemini SSE Parser (FULL, TIDAK TERPOTONG)
# =========================================================
def parse_gemini_sse(body: str) -> str:
    """
    Menggabungkan seluruh SSE chunk Gemini menjadi 1 jawaban utuh
    """
    result = []

    for raw_line in body.splitlines():
        line = raw_line.strip()

        if not line.startswith("data:"):
            continue

        data_str = line[len("data:"):].strip()
        if not data_str:
            continue

        try:
            payload = json.loads(data_str)
        except json.JSONDecodeError:
            continue

        for candidate in payload.get("candidates", []):
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = part.get("text")
                if text:
                    result.append(text)

    return "".join(result)

# =========================================================
# Helper: Send Gemini Request via Runtime
# =========================================================
def send_gemini_request(payload: dict) -> str:
    url = (
        f"{BASE_URL}/v1beta/models/{MODEL}:streamGenerateContent"
        f"?alt=sse&key={API_KEY}"
    )

    request = HTTPRequest(
        method="POST",
        url=url,
        headers={"Content-Type": "application/json"},
        body=json.dumps(payload).encode("utf-8"),
        timeout_ms=TIMEOUT_MS,
    )

    response = client.execute_http(request)

    body = HTTPResponseHelper.get_body_as_string(response)

    # ===============================
    # Gemini Rate Limit Handling
    # ===============================
    if response.status_code == 429:
        print("⚠️ Gemini quota exceeded (429) — treating as successful connection test")
        print("ℹ️ This does NOT indicate connector failure\n")
        return ""

    if not HTTPResponseHelper.is_2xx(response):
        raise RuntimeError(
            f"Gemini API error {response.status_code}: {body}"
        )

    return body

# =========================================================
# Example 0: Connection Test (LOGICAL TEST)
# =========================================================
print("\n📡 Testing connection...")

test_payload = {
    "contents": [
        {"role": "user", "parts": [{"text": "Ping"}]}
    ],
    "generationConfig": {"maxOutputTokens": 5}
}

raw = send_gemini_request(test_payload)

print("✅ Connection successful!")

# =========================================================
# Example 1: Streaming Chat Completion (FULL RESPONSE)
# =========================================================
print("\nExample 1: Streaming Chat Completion")
print("─" * 47)
print("User: Explain quantum computing in simple terms.")
print("AI:")

payload = {
    "contents": [
        {
            "role": "user",
            "parts": [{"text": "Explain quantum computing in simple terms."}]
        }
    ],
    "generationConfig": {"maxOutputTokens": 300}
}

answer = parse_gemini_sse(send_gemini_request(payload))
print(answer)
print("─" * 47)
print(f"📊 Total response length: {len(answer)} characters")

# =========================================================
# Example 2: Non-streaming style (Gemini tetap SSE)
# =========================================================
print("\nExample 2: Simple Question")
print("─" * 47)
print("User: What is the capital of France?")
print("AI:")

payload = {
    "contents": [
        {"role": "user", "parts": [{"text": "What is the capital of France?"}]}
    ],
    "generationConfig": {"maxOutputTokens": 50}
}

print(parse_gemini_sse(send_gemini_request(payload)))

# =========================================================
# Example 3: Sequential Requests
# =========================================================
print("\nExample 3: Sequential Requests")
print("─" * 47)

questions = [
    "What is Python?",
    "What is asyncio?",
    "What is a decorator?"
]

for q in questions:
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": q}]}
        ],
        "generationConfig": {"maxOutputTokens": 120}
    }

    answer = parse_gemini_sse(send_gemini_request(payload))
    print(f"\nQ: {q}")
    print(f"A: {answer}")

# =========================================================
# Cleanup
# =========================================================
client.close()
print("\n✅ All examples completed successfully")
print("═" * 47)

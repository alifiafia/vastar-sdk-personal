#!/usr/bin/env python3
"""Test Gemini Connector with RAI Simulator"""

import sys
import json

# Use local SDK
sys.path.insert(0, '../../sdk-python')

from vastar_connector_sdk import (
    RuntimeClient,
    HTTPRequest,
    RuntimeConfig,
    HTTPResponseHelper,
    SSEParser
)

# =========================================================
# Banner
# =========================================================
print("🤖 Gemini Stream Connector Demo - Python")
print("═" * 61)
print()

print("🧪 Using RAI Simulator")
print("🔗 Base URL: http://localhost:4545")
print()

# =========================================================
# Create & Connect Client
# =========================================================
config = RuntimeConfig(tenant_id="gemini-connector", timeout_ms=60000)
client = RuntimeClient(config)
client.connect()

# =========================================================
# Helper: Build Gemini Payload
# =========================================================
def make_payload(text: str):
    return {
        "contents": [
            { "parts": [ { "text": text } ] }
        ]
    }

# =========================================================
# Example 0: Test Connection
# =========================================================
print("📡 Testing connection...")

request = HTTPRequest(
    method="POST",
    url="http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent",
    headers={"Content-Type": "application/json"},
    body=json.dumps(make_payload("Test connection")).encode("utf-8"),
    timeout_ms=10000,
)

response = client.execute_http(request)

body_str = HTTPResponseHelper.get_body_as_string(response)

print("✅ Connection successful!")
data = json.loads(body_str)
preview = data["candidates"][0]["content"]["parts"][0]["text"]
print(f"   Preview: {preview[:100]}...\n")

# =========================================================
# Example 1: Content Generation
# =========================================================
print("Example 1: Content Generation")
print("─" * 61)
print("User: Explain quantum computing in simple terms.")
print("AI: ")

request = HTTPRequest(
    method="POST",
    url="http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent",
    headers={"Content-Type": "application/json"},
    body=json.dumps(make_payload("Explain quantum computing in simple terms.")).encode("utf-8"),
    timeout_ms=60000,
)

response = client.execute_http(request)

if HTTPResponseHelper.is_2xx(response):
    data = json.loads(HTTPResponseHelper.get_body_as_string(response))
    answer = data["candidates"][0]["content"]["parts"][0]["text"]
    print(answer)
    print("─" * 61)
    print(f"📊 Total response length: {len(answer)} characters")
else:
    print(f"❌ Error: {response.status_code}")

print()

# =========================================================
# Example 2: Factual Question
# =========================================================
print("Example 2: Factual Question")
print("─" * 61)
print("User: What is the capital of France?")
print("AI: ")

request = HTTPRequest(
    method="POST",
    url="http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent",
    headers={"Content-Type": "application/json"},
    body=json.dumps(make_payload("What is the capital of France?")).encode("utf-8"),
    timeout_ms=60000,
)

response = client.execute_http(request)

if HTTPResponseHelper.is_2xx(response):
    data = json.loads(HTTPResponseHelper.get_body_as_string(response))
    print(data["candidates"][0]["content"]["parts"][0]["text"])
else:
    print(f"❌ Error: {response.status_code}")

print()

# =========================================================
# Example 3: Sequential Requests
# =========================================================
print("Example 3: Sequential Requests")
print("─" * 61)

questions = [
    "What is Python?",
    "What is asyncio?",
    "What is a decorator?"
]

for q in questions:
    print(f"Q: {q}")

    request = HTTPRequest(
        method="POST",
        url="http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent",
        headers={"Content-Type": "application/json"},
        body=json.dumps(make_payload(q)).encode("utf-8"),
        timeout_ms=60000,
    )

    response = client.execute_http(request)

    if HTTPResponseHelper.is_2xx(response):
        data = json.loads(HTTPResponseHelper.get_body_as_string(response))
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        print(f"A: {answer[:120]}...")
    else:
        print(f"❌ Error: {response.status_code}")
    print()


# =========================================================
# Example 4: Streaming (SSE)
# =========================================================
print("Example 4: Streaming SSE")
print("─" * 61)
print("User: Explain how neural networks learn.")
print("AI: ")

request = HTTPRequest(
    method="POST",
    url="http://localhost:4545/v1beta/models/gemini-2.5-flash:streamGenerateContent?alt=sse",
    headers={"Content-Type": "application/json"},
    body=json.dumps(make_payload("Explain how neural networks learn.")).encode("utf-8"),
    timeout_ms=60000,
)

response = client.execute_http(request)

if HTTPResponseHelper.is_2xx(response):
    raw = HTTPResponseHelper.get_body_as_string(response)

    parser = SSEParser()

    # parse full SSE payload
    events = parser.parse(raw)

    for event in events:
        if event.data == "[DONE]":
            break

        payload = json.loads(event.data)
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        print(text, end="", flush=True)

    print("\n" + "─" * 61)
else:
    print(f"❌ Error: {response.status_code}")


print("═" * 61)
print("✅ All examples completed successfully!")

client.close()

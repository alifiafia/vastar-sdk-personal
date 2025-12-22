#!/usr/bin/env python3
"""Test OpenAI Connector with Simulator"""
import sys
import json
sys.path.insert(0, '../../sdk-python')
from vastar_connector_sdk import (
    RuntimeClient, 
    HTTPRequest, 
    RuntimeConfig, 
    HTTPResponseHelper,
    SSEParser
)
print("🤖 OpenAI Stream Connector Demo - Python")
print("═" * 61)
print()
# Create client
print("🧪 Using RAI Simulator")
print("🔗 Base URL: http://localhost:4545")
print()
config = RuntimeConfig(tenant_id="openai-connector", timeout_ms=60000)
client = RuntimeClient(config)
# Connect
client.connect()
# Example 1: Test connection
print("📡 Testing connection...")
payload = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Test connection"}],
    "stream": False,
    "max_tokens": 10,
}
request = HTTPRequest(
    method="POST",
    url="http://localhost:4545/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key",
    },
    body=json.dumps(payload).encode("utf-8"),
    timeout_ms=10000,
)
response = client.execute_http(request)
body_str = HTTPResponseHelper.get_body_as_string(response)
if body_str.startswith("data:"):
    print("✅ Connection successful! (SSE stream detected)")
    print(f"   Response preview: {body_str[:100]}...")
else:
    print("✅ Connection successful!")
    data = json.loads(body_str)
    print(f"   Response: {json.dumps(data)[:100]}...")
print()
# Example 1: Streaming Chat Completion
print("Example 1: Streaming Chat Completion")
print("─" * 61)
print("User: Explain quantum computing in simple terms.")
print("AI: ")
payload = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    "stream": True,
}
request = HTTPRequest(
    method="POST",
    url="http://localhost:4545/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key",
    },
    body=json.dumps(payload).encode("utf-8"),
    timeout_ms=60000,
)
response = client.execute_http(request)
if HTTPResponseHelper.is_2xx(response):
    sse_data = HTTPResponseHelper.get_body_as_string(response)
    full_response = SSEParser.parse_stream(sse_data)
    print(full_response)
    print("─" * 61)
    print(f"📊 Total response length: {len(full_response)} characters")
else:
    print(f"❌ Error: {response.status_code}")
print()
# Example 2: Non-Streaming Chat Completion
print("Example 2: Non-Streaming Chat Completion")
print("─" * 61)
print("User: What is the capital of France?")
print("AI: ")
payload = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": False,
}
request = HTTPRequest(
    method="POST",
    url="http://localhost:4545/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key",
    },
    body=json.dumps(payload).encode("utf-8"),
    timeout_ms=60000,
)
response = client.execute_http(request)
if HTTPResponseHelper.is_2xx(response):
    body_str = HTTPResponseHelper.get_body_as_string(response)
    if body_str.startswith("data:"):
        # Simulator returns SSE even for non-streaming
        answer = SSEParser.parse_stream(body_str)
    else:
        data = json.loads(body_str)
        answer = data["choices"][0]["message"]["content"]
    print(answer)
else:
    print(f"❌ Error: {response.status_code}")
print()
# Example 3: Sequential Requests
print("Example 3: Sequential Requests")
print("─" * 61)
questions = [
    "What is Python?",
    "What is asyncio?",
    "What is a decorator?",
]
for question in questions:
    print(f"Q: {question}")
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": question}],
        "stream": False,
    }
    request = HTTPRequest(
        method="POST",
        url="http://localhost:4545/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer dummy-key",
        },
        body=json.dumps(payload).encode("utf-8"),
        timeout_ms=60000,
    )
    response = client.execute_http(request)
    if HTTPResponseHelper.is_2xx(response):
        body_str = HTTPResponseHelper.get_body_as_string(response)
        if body_str.startswith("data:"):
            answer = SSEParser.parse_stream(body_str)
        else:
            data = json.loads(body_str)
            answer = data["choices"][0]["message"]["content"]
        print(f"A: {answer[:100]}...")
    print()
print("═" * 61)
print("✅ All examples completed successfully!")
client.close()

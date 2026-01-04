#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '../../sdk-python')
print("🚀 Testing Python SDK...")
from vastar_connector_sdk import RuntimeClient, HTTPRequest, RuntimeConfig, HTTPResponseHelper
# Create client
print("Creating client...")
config = RuntimeConfig(tenant_id="test")
client = RuntimeClient(config)
# Connect
print("Connecting...")
client.connect()
# Test request
print("Making test request to simulator...")
request = HTTPRequest(
    method="POST",
    url="http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent",

    headers={"Content-Type": "application/json"},
    body=b'{"contents":[{"parts":[{"text":"Hello from test_simple"}]}]}',
)
response = client.execute_http(request)
print(f"✅ Response status: {response.status_code}")
body = HTTPResponseHelper.get_body_as_string(response)
print(f"📦 Response body (first 100 chars): {body[:100]}...")
client.close()
print("✅ Test completed!")

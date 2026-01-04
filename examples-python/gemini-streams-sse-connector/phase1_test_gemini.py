#!/usr/bin/env python3
import sys, json
sys.path.insert(0, '../../sdk-python')

from vastar_connector_sdk import RuntimeClient, HTTPRequest, RuntimeConfig, HTTPResponseHelper

print("=== Phase 1 | Gemini via Vastar Runtime ===")

config = RuntimeConfig(timeout_ms=60000)
client = RuntimeClient(config)
client.connect()

payload = {
    "contents": [{
        "role": "user",
        "parts": [{"text": "Explain Artificial Intelligence in simple terms."}]
    }]
}

request = HTTPRequest(
    method="POST",
    url="http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent",
    headers={"Content-Type": "application/json"},
    body=json.dumps(payload).encode("utf-8"),
    timeout_ms=60000,
)

print("Sending request...")
response = client.execute_http(request)

if HTTPResponseHelper.is_2xx(response):
    body = HTTPResponseHelper.get_body_as_string(response)
    data = json.loads(body)
    answer = data["candidates"][0]["content"]["parts"][0]["text"]

    print("\nGemini says:\n")
    print(answer)
else:
    print("Error:", response.status_code, HTTPResponseHelper.get_body_as_string(response))

client.close()

#!/usr/bin/env python3
"""
Pure Gemini HTTP Client Demo
Testing Gemini via RAI Simulator
"""

import requests
import json
import time

URL = "http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent"

print("\n🤖 Gemini HTTP Client Demo")
print("═" * 60)
print("🔗 Endpoint:", URL)
print()

prompt = "Explain Artificial Intelligence in simple terms."

payload = {
    "contents": [
        {
            "role": "user",
            "parts": [{"text": prompt}]
        }
    ]
}

print("🧑 User :", prompt)
print("📡 Sending request...")

start = time.time()
response = requests.post(URL, json=payload, timeout=30)
elapsed = (time.time() - start) * 1000

print(f"⏱️  Response Time: {elapsed:.2f} ms")

if response.status_code != 200:
    print("❌ Error:", response.status_code)
    print(response.text)
    exit(1)

data = response.json()
answer = data["candidates"][0]["content"]["parts"][0]["text"]

print("\n🤖 Gemini:")
print(answer)

print("\n" + "═" * 60)
print("✅ Demo completed successfully\n")

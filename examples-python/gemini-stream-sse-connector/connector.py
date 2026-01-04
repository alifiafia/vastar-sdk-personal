# connector.py
"""
Gemini Stream SSE Connector - Vastar
Connector entry point for Workflow Engine
"""

import os
import json
import yaml
import sys

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
# Load config.yaml (WAJIB - tidak diubah)
# =========================================================
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

GEMINI_CFG = cfg["gemini"]
RUNTIME_CFG = cfg["runtime"]

BASE_URL = GEMINI_CFG["base_url"]
MODEL = GEMINI_CFG["model"]
TIMEOUT_MS = GEMINI_CFG["timeout_ms"]

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")

# =========================================================
# Runtime Client (Connector Runtime Boundary)
# =========================================================
_client = RuntimeClient(
    RuntimeConfig(
        tenant_id=RUNTIME_CFG["tenant_id"],
        workspace_id=RUNTIME_CFG["workspace_id"],
        timeout_ms=RUNTIME_CFG["timeout_ms"],
    )
)

_client.connect()

# =========================================================
# Gemini SSE Parser (FULL response)
# =========================================================
def _parse_gemini_sse(body: str) -> str:
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
# Internal HTTP call via Runtime
# =========================================================
def _call_gemini(payload: dict) -> str:
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

    response = _client.execute_http(request)
    body = HTTPResponseHelper.get_body_as_string(response)

    if response.status_code == 429:
        # Rate limit dianggap sukses koneksi
        return ""

    if not HTTPResponseHelper.is_2xx(response):
        raise RuntimeError(
            f"Gemini API error {response.status_code}: {body}"
        )

    return _parse_gemini_sse(body)

# =========================================================
# 🚀 CONNECTOR ENTRY POINT (WAJIB)
# =========================================================
def handle(input: dict) -> dict:
    """
    Entry point yang dipanggil Workflow Engine
    """

    prompt = input.get("prompt")
    if not prompt:
        raise ValueError("Missing required field: prompt")

    max_tokens = input.get("max_tokens", 256)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens
        }
    }

    result = _call_gemini(payload)

    return {
        "text": result
    }

# =========================================================
# Optional cleanup hook
# =========================================================
def close():
    _client.close()

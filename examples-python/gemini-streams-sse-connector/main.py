#!/usr/bin/env python3
import os, sys, json, yaml, struct, time, requests, flatbuffers

sys.path.insert(0, "../../sdk-python")

from vastar_connector_sdk.Vastar.Connector.Ipc.ExecuteRequest import ExecuteRequest
from vastar_connector_sdk.Vastar.Connector.Ipc.ExecuteResponse import ExecuteResponse
from vastar_connector_sdk.types import ErrorClass


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def send_response(w, request_id, payload, done=True):
    builder = flatbuffers.Builder(1024)
    body = json.dumps(payload).encode()
    body_offset = builder.CreateByteVector(body)

    ExecuteResponse.Start(builder)
    ExecuteResponse.AddRequestId(builder, request_id)
    ExecuteResponse.AddErrorClass(builder, ErrorClass.SUCCESS)
    ExecuteResponse.AddPayload(builder, body_offset)
    ExecuteResponse.AddDone(builder, done)

    resp = ExecuteResponse.End(builder)
    builder.Finish(resp)

    buf = builder.Output()
    w.write(struct.pack("<I", len(buf)))
    w.write(buf)
    w.flush()


def call_gemini(cfg, prompt):
    if cfg["simulator"]["enabled"]:
        url = f"{cfg['simulator']['base_url']}/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {"Content-Type": "application/json"}
    else:
        url = f"{cfg['gemini']['base_url']}/v1beta/models/{cfg['gemini']['model']}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('GEMINI_API_KEY')}"
        }

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


def handle(req, w, cfg):
    try:
        url = req.Url().decode()
        if not url.startswith("gemini://"):
            raise Exception(f"Unsupported URL: {url}")

        body = json.loads(req.PayloadAsNumpy().tobytes().decode())
        prompt = body.get("prompt", "")

        log(f"Request: {prompt}")

        result = call_gemini(cfg, prompt)

        response = {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": result
        }

        send_response(w, req.RequestId(), response)

    except Exception as e:
        log(f"ERROR: {e}")
        send_response(w, req.RequestId(), {"status": 500, "body": str(e)})


def read_frame(r):
    h = r.read(4)
    if not h:
        return None
    size = struct.unpack("<I", h)[0]
    return r.read(size)


def main():
    cfg = load_config()
    log("Gemini Connector started")
    log("Registering scheme: gemini://")


    r = sys.stdin.buffer
    w = sys.stdout.buffer

    while True:
        frame = read_frame(r)
        if not frame:
            break
        req = ExecuteRequest.GetRootAs(frame, 0)
        handle(req, w, cfg)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os, sys, json, yaml, struct, time, asyncio, flatbuffers, httpx, signal

sys.path.insert(0, "../../sdk-python")

from vastar_connector_sdk.Vastar.Connector.Ipc.ExecuteRequest import ExecuteRequest
from vastar_connector_sdk.Vastar.Connector.Ipc.ExecuteResponse import ExecuteResponse
from vastar_connector_sdk.types import ErrorClass

# ==========================================================
# STABLE TUNING PARAMETERS
# ==========================================================
MAX_INFLIGHT_BASE = 80
MIN_INFLIGHT = 30
MAX_INFLIGHT = MAX_INFLIGHT_BASE
MAX_QUEUE = 200

HTTP_TIMEOUT = None
MAX_RETRY = 2
LATENCY_THRESHOLD = 10000
STEP = 4

# ==========================================================
# Globals
# ==========================================================
shutting_down = False
inflight = 0
recent_latencies = []

writer_lock = asyncio.Lock()
inflight_lock = asyncio.Lock()
latency_lock = asyncio.Lock()

# ==========================================================
# Dynamic Semaphore
# ==========================================================
class DynamicSemaphore:
    def __init__(self, value):
        self._value = value
        self._semaphore = asyncio.Semaphore(value)
        self._lock = asyncio.Lock()

    async def acquire(self):
        await self._semaphore.acquire()

    def release(self):
        self._semaphore.release()

    async def resize(self, new_value):
        async with self._lock:
            delta = new_value - self._value
            self._value = new_value
            if delta > 0:
                for _ in range(delta):
                    self._semaphore.release()

semaphore = DynamicSemaphore(MAX_INFLIGHT)

# ==========================================================
# Circuit Breaker
# ==========================================================
class CircuitBreaker:
    def __init__(self, fail_threshold=12, reset_after=10):
        self.failures = 0
        self.fail_threshold = fail_threshold
        self.open_until = 0
        self.reset_after = reset_after

    def allow(self):
        return time.time() >= self.open_until

    def success(self):
        self.failures = 0

    def failure(self):
        self.failures += 1
        if self.failures >= self.fail_threshold:
            self.open_until = time.time() + self.reset_after
            self.failures = 0

breaker = CircuitBreaker()

# ==========================================================
# Utilities
# ==========================================================
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)

def load_config():
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)

    if cfg["gemini"]["api_key"].startswith("${"):
        cfg["gemini"]["api_key"] = os.environ.get("GEMINI_API_KEY")

    return cfg

# ==========================================================
# Adaptive Concurrency
# ==========================================================
async def adjust_concurrency():
    global MAX_INFLIGHT

    async with latency_lock:
        if not recent_latencies:
            return
        avg = sum(recent_latencies) / len(recent_latencies)

    new_value = MAX_INFLIGHT

    if avg > LATENCY_THRESHOLD:
        new_value = max(MIN_INFLIGHT, new_value - STEP)
    elif avg < LATENCY_THRESHOLD * 0.65:
        new_value = min(MAX_INFLIGHT_BASE, new_value + STEP)

    if abs(new_value - MAX_INFLIGHT) >= STEP:
        MAX_INFLIGHT = new_value
        await semaphore.resize(new_value)
        log(f"Concurrency → {new_value}")

# ==========================================================
# Flatbuffer Response
# ==========================================================
def build_response(request_id, payload):
    builder = flatbuffers.Builder(1024)
    body = json.dumps(payload).encode()
    body_offset = builder.CreateByteVector(body)

    ExecuteResponse.Start(builder)
    ExecuteResponse.AddRequestId(builder, request_id)
    ExecuteResponse.AddErrorClass(builder, ErrorClass.SUCCESS)
    ExecuteResponse.AddPayload(builder, body_offset)
    ExecuteResponse.AddDone(builder, True)

    resp = ExecuteResponse.End(builder)
    builder.Finish(resp)

    buf = builder.Output()
    return struct.pack("<I", len(buf)) + buf

# ==========================================================
# Gemini Call — HARD SECURITY GATE
# ==========================================================
async def call_gemini(cfg, prompt, client):
    if cfg["simulator"]["enabled"]:
        base = cfg["simulator"]["base_url"]
        if not base.startswith("http://127.0.0.1"):
            raise RuntimeError("Simulator must be localhost only")

        url = f"{base}/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {"Content-Type": "application/json"}
    else:
        raise RuntimeError("External access blocked by security policy")

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for _ in range(MAX_RETRY + 1):
        try:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except:
            await asyncio.sleep(1)

# ==========================================================
# Handler
# ==========================================================
async def handle(req, writer, cfg, client):
    global inflight

    if shutting_down:
        return

    start = time.time()

    async with inflight_lock:
        if inflight >= MAX_QUEUE:
            writer.write(build_response(req.RequestId(), {"status": 503, "body": "Overloaded"}))
            await writer.drain()
            return
        inflight += 1

    try:
        if not breaker.allow():
            raise Exception("Circuit open")

        body = json.loads(req.PayloadAsNumpy().tobytes().decode())
        prompt = body.get("prompt", "")

        answer = await asyncio.wait_for(call_gemini(cfg, prompt, client), timeout=70)
        breaker.success()

        response = {"status": 200, "headers": {"Content-Type": "application/json"}, "body": answer}
    except:
        breaker.failure()
        response = {"status": 500, "body": "Internal Error"}

    async with writer_lock:
        writer.write(build_response(req.RequestId(), response))
        await writer.drain()

    latency = (time.time() - start) * 1000

    async with latency_lock:
        recent_latencies.append(latency)
        if len(recent_latencies) > 80:
            recent_latencies.pop(0)

    await adjust_concurrency()

    async with inflight_lock:
        inflight -= 1

# ==========================================================
# Worker Wrapper
# ==========================================================
async def worker(req, writer, cfg, client):
    await semaphore.acquire()
    try:
        await handle(req, writer, cfg, client)
    finally:
        semaphore.release()

# ==========================================================
# Main
# ==========================================================
async def main():
    cfg = load_config()
    global HTTP_TIMEOUT
    HTTP_TIMEOUT = cfg["gemini"]["timeout_ms"] / 1000

    log("🚀 Gemini Connector (Production) running")

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    # ==========================================================
    # IPC ONLY when real Vastar runtime is present
    # ==========================================================
    enable_ipc = os.environ.get("VASTAR_RUNTIME", "") == "1"

    if enable_ipc:
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, loop)
    else:
        reader = None
        writer = None

    client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=300, max_keepalive_connections=120),
        timeout=httpx.Timeout(HTTP_TIMEOUT)
    )

    while not shutting_down:
        if not enable_ipc:
            await asyncio.sleep(0.1)
            continue

        header = await reader.readexactly(4)
        size = struct.unpack("<I", header)[0]
        frame = await reader.readexactly(size)
        req = ExecuteRequest.GetRootAs(frame, 0)
        asyncio.create_task(worker(req, writer, cfg, client))

    log("🛑 Draining inflight requests...")

    while True:
        async with inflight_lock:
            if inflight == 0:
                break
        await asyncio.sleep(0.1)

    await client.aclose()
    log("✅ Shutdown complete")


# ==========================================================
def shutdown():
    global shutting_down
    if not shutting_down:
        log("🧯 Shutdown signal received")
        shutting_down = True

if __name__ == "__main__":
    asyncio.run(main())

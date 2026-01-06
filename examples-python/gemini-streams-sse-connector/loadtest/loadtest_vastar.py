import sys, json, time, asyncio, os
from statistics import mean
from collections import deque
from contextlib import contextmanager

# Import Vastar SDK
sys.path.insert(0, '../../../sdk-python')
from vastar_connector_sdk import (
    RuntimeClient,
    HTTPRequest,
    RuntimeConfig,
    HTTPResponseHelper
)

# ===============================
# CONFIG
# ===============================
TOTAL        = 100
CONCURRENCY  = 50
WARMUP       = 10
TIMEOUT_MS   = 60000
URL = "http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent"

latencies = deque()
success   = 0
failed    = 0
stats_lock = asyncio.Lock()

# ===============================
# STDOUT SUPPRESSION
# ===============================
@contextmanager
def suppress_stdout():
    fd = sys.stdout.fileno()
    saved = os.dup(fd)
    with open(os.devnull, "w") as null:
        os.dup2(null.fileno(), fd)
    try:
        yield
    finally:
        os.dup2(saved, fd)
        os.close(saved)

# ===============================
# REQUEST BUILDER
# ===============================
def build_request(i):
    payload = {
        "contents": [
            {"parts": [{"text": f"Explain AI {i}"}]}
        ]
    }
    return HTTPRequest(
        method="POST",
        url=URL,
        headers={"Content-Type": "application/json"},
        body=json.dumps(payload).encode(),
        timeout_ms=TIMEOUT_MS,
    )

# ===============================
# WORKER
# ===============================
def worker(client, i):
    start = time.time()
    try:
        response = client.execute_http(build_request(i))
        ok = HTTPResponseHelper.is_2xx(response)
    except Exception:
        ok = False
    elapsed = (time.time() - start) * 1000
    return ok, elapsed

# ===============================
# MAIN
# ===============================
async def main():
    global success, failed

    print(f"\n🚀  Memulai Vastar LoadTest (Concurrency={CONCURRENCY})")
    print("⏳ Progress: ", end="", flush=True)

    config = RuntimeConfig(timeout_ms=TIMEOUT_MS)

    clients = [RuntimeClient(config) for _ in range(CONCURRENCY)]

    # Silent connect
    with suppress_stdout():
        for c in clients:
            c.connect()
    print("🐧 Connected via Unix Socket")

    # Warmup
    for i in range(WARMUP):
        await asyncio.to_thread(worker, clients[0], i)

    sem = asyncio.Semaphore(CONCURRENCY)
    start_all = time.time()

    async def run(i):
        global success, failed
        async with sem:
            ok, t = await asyncio.to_thread(worker, clients[i % CONCURRENCY], i)
            async with stats_lock:
                latencies.append(t)
                success += int(ok)
                failed += int(not ok)
                print("█", end="", flush=True)

    await asyncio.gather(*(run(i) for i in range(TOTAL)))

    total_time = (time.time() - start_all) * 1000

    # Silent close
    with suppress_stdout():
        for c in clients:
            c.close()
    print("\n✅ Connection closed")

    lat_sorted = sorted(latencies)

    # Report
    print("\n📊 HASIL LOAD TEST: VASTAR CONNECTOR")
    print("-" * 55)
    print(f"Requests      : {TOTAL}")
    print(f"Success       : {success}")
    print(f"Failed        : {failed}")
    print(f"Total         : {int(total_time)} ms")
    print(f"Avg           : {mean(lat_sorted):.2f} ms")
    print(f"Min (Latency) : {min(lat_sorted):.2f} ms")
    print(f"Max (Latency) : {max(lat_sorted):.2f} ms")
    print(f"P50           : {lat_sorted[int(TOTAL * 0.50)]:.2f} ms")
    print(f"P95           : {lat_sorted[int(TOTAL * 0.95) - 1]:.2f} ms")
    print("-" * 55)

asyncio.run(main())

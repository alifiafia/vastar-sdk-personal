import sys, json, time, asyncio, builtins
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

sys.path.insert(0, '../../../sdk-python')
from vastar_connector_sdk import RuntimeClient, HTTPRequest, RuntimeConfig, HTTPResponseHelper

# ===============================
# CONFIG
# ===============================
TOTAL = 100
CONCURRENCY = 10
URL = "http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent"

latencies = []
success = 0
failed = 0

# ===============================
# SILENCE SDK OUTPUT SAFELY
# ===============================
def silent_call(fn):
    def wrapper(*a, **k):
        old_print = builtins.print
        builtins.print = lambda *x, **y: None
        try:
            return fn(*a, **k)
        finally:
            builtins.print = old_print
    return wrapper

# ===============================
# WORKER
# ===============================
@silent_call
def worker(i):
    client = RuntimeClient(RuntimeConfig(timeout_ms=60000))
    client.connect()

    payload = {"contents": [{"parts": [{"text": f"Explain AI {i}"}]}]}

    request = HTTPRequest(
        method="POST",
        url=URL,
        headers={"Content-Type": "application/json"},
        body=json.dumps(payload).encode(),
        timeout_ms=60000,
    )

    start = time.time()
    try:
        response = client.execute_http(request)
        ok = HTTPResponseHelper.is_2xx(response)
    except:
        ok = False

    elapsed = (time.time() - start) * 1000
    client.close()
    return ok, elapsed

# ===============================
# MAIN
# ===============================
async def main():
    global success, failed

    print(f"\n🚀 Memulai Load Test Vastar (Konkursensi: {CONCURRENCY})...")
    print("⏳ Progress: ", end="", flush=True)

    start_all = time.time()
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        results = await asyncio.gather(
            *[loop.run_in_executor(pool, worker, i) for i in range(TOTAL)]
        )

    total_time = (time.time() - start_all) * 1000

    for ok, t in results:
        latencies.append(t)
        success += ok
        failed += not ok
        print("█", end="", flush=True)

    lat_sorted = sorted(latencies)

    print("\n\n📊 HASIL PENGUJIAN: VASTAR CONNECTOR")
    print("-" * 50)
    print(f"- Total Request   : {TOTAL}")
    print(f"- Berhasil (2xx)  : {success}")
    print(f"- Gagal/Error    : {failed}")
    print(f"- Total Waktu    : {int(total_time)} ms")
    print(f"- Rata-rata      : {mean(latencies):.2f} ms/req")
    print(f"- Min Latency    : {min(lat_sorted):.2f} ms")
    print(f"- Max Latency    : {max(lat_sorted):.2f} ms")
    print(f"- P50 (Median)   : {lat_sorted[int(TOTAL*0.5)]:.2f} ms")
    print(f"- P95            : {lat_sorted[int(TOTAL*0.95)-1]:.2f} ms")
    print("-" * 50)

asyncio.run(main())

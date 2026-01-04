import asyncio, time, httpx
from statistics import mean
import builtins

TOTAL = 100
CONCURRENCY = 20
URL = "http://localhost:4545/v1beta/models/gemini-2.5-flash:generateContent"

latencies = []
success = 0
failed = 0

async def worker(i, client):
    payload = {"contents": [{"parts": [{"text": f"Explain AI {i}"}]}]}

    start = time.time()
    try:
        r = await client.post(URL, json=payload, timeout=60)
        ok = r.status_code == 200
    except:
        ok = False

    elapsed = (time.time() - start) * 1000
    return ok, elapsed


async def main():
    global success, failed

    print(f"\n🚀 Memulai Pure Python Load Test (Konkursensi: {CONCURRENCY})...")
    print("⏳ Progress: ", end="", flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    start_all = time.time()

    async with httpx.AsyncClient() as client:
        async def run(i):
            async with sem:
                ok, t = await worker(i, client)
                latencies.append(t)
                print("█", end="", flush=True)
                return ok

        results = await asyncio.gather(*[run(i) for i in range(TOTAL)])

    total_time = (time.time() - start_all) * 1000

    for r in results:
        success += r
        failed += not r

    lat_sorted = sorted(latencies)

    print("\n\n📊 HASIL PENGUJIAN: PURE PYTHON")
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

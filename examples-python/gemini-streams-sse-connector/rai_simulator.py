from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn, time

app = FastAPI()

@app.post("/v1beta/models/gemini-2.5-flash:generateContent")
async def generate(req: Request):
    data = await req.json()
    prompt = data["contents"][0]["parts"][0]["text"]
    time.sleep(0.1)  # simulasi latency

    return JSONResponse({
        "candidates": [{
            "content": {
                "parts": [{"text": f"[SIMULATOR] Answer to: {prompt}"}]
            }
        }]
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4545)

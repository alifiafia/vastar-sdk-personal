from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time

app = FastAPI()

# -------------------------------
# Mini knowledge base (offline AI)
# -------------------------------
def smart_answer(prompt: str) -> str:
    p = prompt.lower()

    if "runtime connector" in p:
        return (
            "A Runtime Connector is a secure communication layer between a workflow engine "
            "and external systems. It isolates failures, prevents uncontrolled side effects, "
            "and guarantees that all external interactions remain safe, observable, and manageable."
        )

    if "gemini" in p:
        return (
            "Gemini AI is a multimodal artificial intelligence system capable of understanding "
            "and generating text, code, and other data formats with strong reasoning ability."
        )

    if "server-sent events" in p or "sse" in p:
        return (
            "Server-Sent Events (SSE) is a streaming technology that allows a server to push "
            "continuous updates to clients over a single persistent HTTP connection."
        )

    if "artificial intelligence" in p or "ai" in p:
        return (
            "Artificial Intelligence (AI) refers to systems that can perform tasks requiring "
            "human-like intelligence, such as learning, reasoning, pattern recognition, and decision making."
        )

    return (
        "This is an important topic in modern computing. The concept you are asking about "
        "plays a major role in scalable systems, automation, and intelligent software design."
    )

# -------------------------------
# Gemini Simulator Endpoint
# -------------------------------
@app.post("/v1beta/models/gemini-2.5-flash:generateContent")
async def generate(req: Request):
    data = await req.json()
    prompt = data["contents"][0]["parts"][0]["text"]

    # simulasi latency
    time.sleep(0.12)

    answer = smart_answer(prompt)

    return JSONResponse({
        "candidates": [{
            "content": {
                "parts": [{"text": answer}]
            }
        }]
    })

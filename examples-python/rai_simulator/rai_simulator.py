from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import json

app = FastAPI()

# ==========================================================
# Mini knowledge base (offline AI)  ← 100% PUNYAMU
# ==========================================================
def smart_answer(prompt: str) -> str:
    p = prompt.lower().strip()

    # ===============================
    # Knowledge: Programming Basics
    # ===============================
    if "python" in p:
        return (
            "Python is a high-level programming language known for its simplicity, readability, "
            "and wide ecosystem. It is commonly used for web development, data science, automation, "
            "artificial intelligence, and many other domains."
        )

    if "asyncio" in p:
        return (
            "Asyncio is a Python library that enables writing concurrent code using the async/await "
            "syntax. It is designed to handle I/O-bound and high-level structured network code efficiently."
        )

    if "decorator" in p:
        return (
            "A decorator is a Python feature that allows you to modify or extend the behavior of a "
            "function or class without changing its original source code."
        )

    # ===============================
    # Knowledge: Systems & Architecture
    # ===============================
    if "runtime connector" in p:
        return (
            "A Runtime Connector is a secure communication layer between a workflow engine and external "
            "systems. It isolates failures, prevents uncontrolled side effects, and ensures all external "
            "interactions remain observable and manageable."
        )

    if "server-sent events" in p or "sse" in p:
        return (
            "Server-Sent Events (SSE) is a web technology that allows a server to push continuous updates "
            "to a client over a single long-lived HTTP connection."
        )

    if "gemini" in p:
        return (
            "Gemini is a multimodal artificial intelligence model capable of understanding and generating "
            "text, code, and other data formats with strong reasoning abilities."
        )

    # ===============================
    # Knowledge: AI
    # ===============================
    if "artificial intelligence" in p or " ai " in f" {p} ":
        return (
            "Artificial Intelligence (AI) refers to computer systems designed to perform tasks that "
            "normally require human intelligence, such as learning, reasoning, pattern recognition, "
            "and decision making."
        )

    # ===============================
    # Default fallback
    # ===============================
    return (
        "This topic is important in modern computing and plays a significant role in system design, "
        "automation, and the development of intelligent software solutions."
    )

# ==========================================================
# Gemini Compatible Endpoint
# ==========================================================
@app.post("/v1beta/models/{model}:generateContent")
async def gemini(model: str, req: Request):
    data = await req.json()
    prompt = data["contents"][0]["parts"][0]["text"]
    await asyncio.sleep(0.05)

    return JSONResponse({
        "candidates": [{
            "content": {
                "parts": [{"text": smart_answer(prompt)}]
            }
        }]
    })

# ==========================================================
# Gemini Streaming SSE Endpoint
# ==========================================================
@app.post("/v1beta/models/{model}:streamGenerateContent")
async def gemini_stream(model: str, req: Request):

    data = await req.json()
    prompt = data["contents"][0]["parts"][0]["text"]

    async def event_generator():
        answer = smart_answer(prompt)

        for word in answer.split():
            payload = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": word + " "}]
                    }
                }]
            }

            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.05)

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ==========================================================
# OpenAI Compatible Endpoint
# ==========================================================
@app.post("/v1/chat/completions")
async def openai(req: Request):
    data = await req.json()
    prompt = data["messages"][-1]["content"]
    await asyncio.sleep(0.05)

    return {
        "choices": [{
            "message": {
                "content": smart_answer(prompt)
            }
        }]
    }

# ==========================================================
# Generic API (future connectors)
# ==========================================================
@app.post("/generate")
async def generic(req: Request):
    data = await req.json()
    prompt = data.get("prompt", "")
    await asyncio.sleep(0.05)
    return {"result": smart_answer(prompt)}

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time
import asyncio

app = FastAPI()

# ===============================
# Mini knowledge base (offline AI)
# ===============================
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

# ===============================
# Gemini-style API Endpoint
# ===============================
@app.post("/v1beta/models/gemini-2.5-flash:generateContent")
async def generate(req: Request):
    data = await req.json()
    prompt = data["contents"][0]["parts"][0]["text"]

    # simulasi latency
    await asyncio.sleep(0.05)

    answer = smart_answer(prompt)

    return JSONResponse({
        "candidates": [{
            "content": {
                "parts": [{"text": answer}]
            }
        }]
    })

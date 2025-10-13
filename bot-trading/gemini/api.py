from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio

gemini = APIRouter()


# Normal REST API endpoint
@gemini.post("/message")
async def receive_message(request: Request):
    data = await request.json()
    message = data.get("message", "")
    reply = f"Received your message: '{message}'"
    return JSONResponse(content={"reply": reply})


# Streaming text endpoint
@gemini.get("/stream")
async def stream_text():
    async def event_generator():
        text_chunks = [
            "Hello there! 👋\n",
            "Streaming from /api/stream endpoint...\n",
            "Each message sent with delay...\n",
            "Done ✅\n",
        ]
        for chunk in text_chunks:
            yield chunk
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/plain")

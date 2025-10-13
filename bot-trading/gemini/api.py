import asyncio
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from gemini.agents_gemini.agentic_agent import MasterGemini

master_gemini = MasterGemini()

gemini = APIRouter()


# Streaming text endpoint
@gemini.get("/stream")
async def stream_text(query: str = Query(..., description="Text to process or stream")):
    async def event_generator():

        for chunk in master_gemini(query):
            for line in chunk.splitlines(keepends=True):
                for char in line:
                    payload = {"character": char}
                    yield f"data: {json.dumps(payload)}\n\n"
                    await asyncio.sleep(0.005)

        yield "event: end\ndata: Stream finished ✅\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

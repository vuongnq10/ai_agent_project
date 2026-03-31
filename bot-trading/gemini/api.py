import asyncio
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from gemini.agents_gemini.agentic_agent import MasterGemini

master_gemini = MasterGemini()

gemini = APIRouter()


@gemini.get("/stream")
async def stream_text(query: str = Query(..., description="Text to process or stream")):
    """Stream a Gemini multi-agent response character by character via SSE."""

    async def event_generator():
        for chunk in master_gemini(query):
            for line in chunk.splitlines(keepends=True):
                for char in line:
                    yield f"data: {json.dumps({'character': char})}\n\n"
                    await asyncio.sleep(0.005)

        yield "event: end\ndata: Stream finished\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

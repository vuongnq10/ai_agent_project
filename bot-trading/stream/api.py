import asyncio
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from stream.stream_factory import get_master_agent

stream = APIRouter()


@stream.get("/{provider}/{model}/stream")
async def stream_text(
    provider: str,
    model: str,
    query: str = Query(..., description="Text to process or stream"),
):
    """Stream a multi-agent response character by character via SSE.

    provider: gemini | claude | chatgpt
    model:    provider-specific model name (e.g. gemini-2.5-flash, sonnet, gpt-4o)
    """
    master = get_master_agent(provider)

    async def event_generator():
        for chunk in master(query, model=model):
            for line in chunk.splitlines(keepends=True):
                for char in line:
                    yield f"data: {json.dumps({'character': char})}\n\n"
                    await asyncio.sleep(0.005)

        yield "event: end\ndata: Stream finished\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

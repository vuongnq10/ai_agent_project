import asyncio
import json
import importlib

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

agentic_module = importlib.import_module('chat-gpt.agents_chatgpt.agentic_agent')
MasterChatGPT = agentic_module.MasterChatGPT

master_chatgpt = MasterChatGPT()

chatgpt = APIRouter()


@chatgpt.get("/{model}/stream")
async def stream_text(
    model: str,
    query: str = Query(..., description="Text to process or stream"),
):
    """Stream a ChatGPT multi-agent response character by character via SSE."""

    async def event_generator():
        for chunk in master_chatgpt(query, model=model):
            for line in chunk.splitlines(keepends=True):
                for char in line:
                    yield f"data: {json.dumps({'character': char})}\n\n"
                    await asyncio.sleep(0.005)

        yield "event: end\ndata: Stream finished\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

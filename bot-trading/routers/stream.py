import asyncio
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse


def _build_registry() -> dict:
    from agents.gemini.agentic_agent import MasterGemini
    from agents.claude.agentic_agent import MasterClaude
    from agents.chat_gpt.agentic_agent import MasterChatGPT

    return {
        "gemini": MasterGemini(),
        "claude": MasterClaude(),
        "chatgpt": MasterChatGPT(),
    }


_registry: dict | None = None


def get_master_agent(provider: str):
    global _registry
    if _registry is None:
        _registry = _build_registry()

    agent = _registry.get(provider)
    if agent is None:
        supported = ", ".join(_registry.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Unknown provider '{provider}'. Supported: {supported}",
        )
    return agent


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

from fastapi import HTTPException


def _build_registry() -> dict:
    from gemini.agentic_agent import MasterGemini
    from claude.agentic_agent import MasterClaude
    from chat_gpt.agentic_agent import MasterChatGPT

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

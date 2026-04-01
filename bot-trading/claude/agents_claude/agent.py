import anthropic

CLAUDE_MODEL = "claude-opus-4-6"

_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


class Agent:
    """Thin wrapper around the Claude messages API with extended thinking."""

    def __call__(self, messages, tools=None, system=None):
        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": 16000,
            "messages": messages,
            "thinking": {"type": "enabled", "budget_tokens": 8000},
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        response = _client.beta.messages.create(
            **kwargs,
            betas=["interleaved-thinking-2025-05-14"],
        )
        return response

"""
Agent wrapper that connects to the local Claude Code CLI (claude terminal)
via the claude_agent_sdk. This replaces the direct Anthropic API call with
a subprocess-backed SDK that talks to the `claude` binary installed on this machine.
"""

import concurrent.futures
import json
from typing import Union

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage, TextBlock

_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Default model used when no model is specified by the caller.
CLAUDE_MODEL = "claude-opus-4-6"


def _messages_to_prompt(messages: list) -> str:
    """
    Flatten a list of chat message dicts into a single prompt string.

    The full conversation history is serialised so Claude has context,
    then a clear instruction to respond only with the routing JSON is
    appended to prevent conversational drift.

    Args:
        messages: List of {"role": str, "content": str | list} dicts.

    Returns:
        A single string prompt ready for claude_agent_sdk query().
    """
    lines: list[str] = []

    lines.append("<conversation>")
    for msg in messages:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")

        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            # Flatten content blocks (tool_result dicts or SDK block objects)
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    btype = block.get("type", "")
                    if btype == "tool_result":
                        parts.append(f"[tool_result]: {block.get('content', '')}")
                    elif btype == "text":
                        parts.append(block.get("text", ""))
                    else:
                        parts.append(json.dumps(block))
                elif hasattr(block, "type"):
                    if block.type == "text":
                        parts.append(block.text)
                    elif block.type == "thinking":
                        parts.append(f"[thinking]: {block.thinking}")
                    else:
                        parts.append(str(block))
                else:
                    parts.append(str(block))
            text = "\n".join(parts)
        else:
            text = str(content)

        lines.append(f"[{role}]: {text}")

    lines.append("</conversation>")
    lines.append(
        "\nBased on the conversation above, respond ONLY with the required JSON object "
        "as described in the system instructions. Do not add any explanation or markdown "
        "around the JSON."
    )

    return "\n".join(lines)


class Agent:
    """
    Thin wrapper around the Claude Agent SDK.

    Instead of calling the Anthropic REST API directly, this class spawns
    the local `claude` CLI process and communicates with it via the SDK.
    This means the agent has access to all built-in Claude Code tools
    and the system_prompt is passed via ClaudeAgentOptions so it takes priority
    over the project CLAUDE.md, ensuring the agent behaves as a trading
    orchestrator rather than as Claude Code.

    Accepts either a plain string prompt or a list of chat message dicts
    (in OpenAI/Anthropic message format). When a list is passed the messages
    are formatted into a single prompt string before being sent to the SDK.
    """

    def __call__(
        self,
        prompt: Union[str, list],
        tools: list | None = None,
        system: str | None = None,
        model: str | None = None,
        allowed_tools: list | None = None,
    ) -> str:
        """
        Send a prompt to the local Claude terminal and return the final text response.

        Args:
            prompt:        The user prompt / question to send, either as a plain
                           string or as a list of message dicts (chat history).
            tools:         (unused) kept for API compatibility.
            system:        Optional system prompt — passed via ClaudeAgentOptions
                           so it overrides CLAUDE.md project context.
            model:         Model ID to use (defaults to CLAUDE_MODEL).
            allowed_tools: List of built-in tool names the agent may use.
                           Defaults to empty list so the agent cannot modify files.

        Returns:
            The final text response from Claude as a plain string.
        """
        # Convert message list to a formatted prompt string if needed.
        # The system instruction is passed separately via ClaudeAgentOptions.
        if isinstance(prompt, list):
            prompt_str = _messages_to_prompt(prompt)
        else:
            prompt_str = str(prompt)

        # Build the options object that configures the CLI session.
        # Passing system_prompt here ensures it overrides the project CLAUDE.md
        # context, so the agent behaves as the trading orchestrator.
        options = ClaudeAgentOptions(
            model=model or CLAUDE_MODEL,
            # No file-system tools — this is a pure LLM reasoning call
            allowed_tools=allowed_tools if allowed_tools is not None else [],
            system_prompt=system or None,
        )

        # The SDK is async-first (anyio-backed); run it in a separate thread
        # so LangGraph sync nodes can call this without event-loop conflicts.
        def run_in_thread():
            return anyio.run(self._run, prompt_str, options)

        future = _THREAD_POOL.submit(run_in_thread)
        return future.result()

    async def _run(self, prompt: str, options: ClaudeAgentOptions) -> str:
        """
        Async coroutine that streams messages from the Claude CLI and collects
        the final result text.

        The SDK yields several message types:
          - AssistantMessage  : intermediate tool calls / thinking steps
          - ResultMessage     : the final answer (stop_reason = "end_turn")
          - SystemMessage     : session metadata (session_id, init info)
        """
        result_text = ""

        # query() returns an async generator; each iteration is one message
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                # ResultMessage.result contains the complete final response
                result_text = message.result
                break
            elif isinstance(message, AssistantMessage):
                # Intermediate assistant turns — collect any text blocks
                # in case ResultMessage is not emitted (e.g. max_turns hit)
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result_text = block.text  # keep the last text seen

        return result_text

from openai import OpenAI
import config

CHATGPT_MODEL = "gpt-4o"

_client = OpenAI(api_key=config.OPEN_API_KEY)


class Agent:
    """Thin wrapper around the OpenAI chat completions API."""

    def __call__(self, messages, tools=None, system=None, model=None):
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        kwargs = {
            "model": model or CHATGPT_MODEL,
            "messages": all_messages,
            "temperature": 0.2,
            "max_tokens": 2048,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = _client.chat.completions.create(**kwargs)
        return response

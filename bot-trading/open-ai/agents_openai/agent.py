import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


class OpenAIAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def __call__(self, messages, system_instruction=None, tools=None):
        """
        Call OpenAI API with messages and optional system instruction and tools

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_instruction: Optional system instruction string
            tools: Optional list of tool definitions for function calling

        Returns:
            OpenAI response object
        """
        # Convert messages to OpenAI format if needed
        openai_messages = self._convert_messages(messages, system_instruction)

        # Prepare API call parameters
        api_params = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        # Add tools if provided
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = "auto"

        try:
            response = self.client.chat.completions.create(**api_params)
            return response
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

    def _convert_messages(self, messages, system_instruction=None):
        """Convert messages to OpenAI format"""
        openai_messages = []

        # Add system instruction if provided
        if system_instruction:
            openai_messages.append({"role": "system", "content": system_instruction})

        # Convert input messages
        if isinstance(messages, list):
            for msg in messages:
                if hasattr(msg, "role") and hasattr(msg, "parts"):
                    # Convert from Gemini format
                    content = ""
                    for part in msg.parts:
                        if hasattr(part, "text"):
                            content += part.text

                    openai_messages.append(
                        {
                            "role": "user" if msg.role == "user" else "assistant",
                            "content": content,
                        }
                    )
                elif isinstance(msg, dict):
                    # Already in OpenAI format
                    openai_messages.append(msg)
                else:
                    # String message
                    openai_messages.append({"role": "user", "content": str(msg)})
        else:
            # Single string message
            openai_messages.append({"role": "user", "content": str(messages)})

        return openai_messages

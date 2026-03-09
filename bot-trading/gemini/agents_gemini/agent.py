import os

from google.genai import Client
from google.genai.types import (
    HttpOptions,
    GenerateContentConfig,
    ThinkingConfig,
)
import config

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = config.API_KEY
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class Agent:
    def __call__(self, contents, tools=None, system_instruction=None):

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=GenerateContentConfig(
                tools=tools,
                thinking_config=ThinkingConfig(include_thoughts=True),
                temperature=0.2,
                seed=42,
                system_instruction=system_instruction,
            ),
        )
        return response

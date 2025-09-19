import os

from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, ThinkingConfig

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class Agent:
    def __call__(self, contents, tools=None):
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=GenerateContentConfig(
                tools=tools,
                thinking_config=ThinkingConfig(include_thoughts=True),
            ),
        )
        return response

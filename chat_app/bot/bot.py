import os

from google.genai import Client
from google.genai.types import HttpOptions, Content, Part

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")

client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class ChatBot:

    def bot_response(self, user_message: str) -> str:
        user_propmpt = Content(role="user", parts=[Part.from_text(text=user_message)])

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[user_propmpt],
        )

        return response.text

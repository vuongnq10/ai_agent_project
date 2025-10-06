import os

from openai import OpenAI

OPENAI_MODEL = "gpt-4o-mini"
OPEN_API_KEY = os.getenv("OPEN_API_KEY")
client = OpenAI(api_key=OPEN_API_KEY)


class OpenAIAgent:
    def __call__(self, prompt, tools=None):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            return response
        except Exception as e:
            return str(e)

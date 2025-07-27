# https://github.com/googleapis/python-genai

import os
from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part
from chatbot.tools.cx_connector import CXConnector

GEMINI_MODEL = "gemini-2.0-flash-001"
API_KEY = os.getenv("GOOGLE_API_KEY")

cx_connector = CXConnector()

client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class Agent:

    def call_agent(self, prompt: str) -> str:
        # history = [Content(role="user", parts=[Part.from_text(text=prompt)])]

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[Content(role="user", parts=[Part.from_text(text=prompt)])],
            config=GenerateContentConfig(tools=[cx_connector.tools]),
        )

        print("🤖 Agent response:", response)

        while True:
            print("🤖 Waiting for function calls...")
            function_calls = []
            function_content = []
            for candidate in response.candidates:
                function_content.append(candidate.content)
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            function_calls.append(part.function_call)

            if not function_calls:
                print("✅ Final result:", response.text)
                return response.text

            # Execute and respond to tool calls
            tool_responses = []
            for func_call in function_calls:
                tool_name = func_call.name
                args = dict(func_call.args)

                try:
                    tool_func = getattr(cx_connector, tool_name)
                    tool_result = tool_func(**args)
                    function_response = Part.from_function_response(
                        name=tool_name,
                        response=tool_result,
                    )
                except (AttributeError, TypeError) as e:
                    function_response = Part.from_text(
                        text=f"Error: Tool {tool_name} not found or not callable. {e}"
                    )
                except Exception as e:
                    function_response = Part.from_text(text=f"Error: {str(e)}")

                tool_responses.append(function_response)

            print("🤖 Tool responses:", tool_responses)

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    Content(role="user", parts=[Part.from_text(text=prompt)]),
                    response.candidates[0].content,
                    tool_responses,
                ],
                config=GenerateContentConfig(tools=[cx_connector.tools]),
            )
            # print("🤖 Agent response after tool call:", response)

    def __call__(self, prompt: str) -> str:
        return self.call_agent(prompt)

# agent.py
import google.generativeai as genai
from chatbot.tools.tool_server import ToolServer
import os
import json

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")


class Agent:
    def __init__(self, api_key=API_KEY):
        # Init Gemini
        genai.configure(api_key=api_key, transport="rest")

        # Init tools
        self.tool_server = ToolServer()

        # Get tool configurations
        tools_config = self.tool_server.get_tools_config()

        # Configure model with tools
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
            tools=tools_config,
        )

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        return self.tool_server.execute_tool(tool_name, **kwargs)

    def call_agent(self, prompt: str) -> str:
        chat = self.model.start_chat()
        response = chat.send_message(prompt)

        while True:
            function_calls = []
            for candidate in response.candidates:
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            function_calls.append(part.function_call)

            if len(function_calls) == 0:
                print("✅ Final result:", response.text)
                return response.text

            tool_responses = []
            for func_call in function_calls:
                tool_name = func_call.name
                args = dict(func_call.args)

                # result = self.execute_tool(tool_name, **args)

                tool_result = self.execute_tool(tool_name, **args)
                tool_responses.append({"name": tool_name, "content": str(tool_result)})

            # Build tool response message
            tool_message = {"role": "function", "parts": []}
            for resp in tool_responses:
                tool_message["parts"].append(
                    {
                        "function_response": {
                            "name": resp["name"],
                            "response": resp["content"],
                        }
                    }
                )

            # Send tool responses to Gemini
            response = chat.send_message(
                part=genai.types.Part(
                    function_response=genai.types.FunctionResponse(
                        name=tool_name,
                        response=tool_result,
                    )
                )
            )
            print("Debug Tool responses:", response)

    def __call__(self, prompt: str) -> str:
        return self.call_agent(prompt)

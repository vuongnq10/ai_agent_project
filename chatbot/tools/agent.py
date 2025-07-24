import os
import google.generativeai as genai
from chatbot.tools.calculator import Calculator
from chatbot.tools.cx_connector import CXConnector

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")


class Agent:
    def __init__(self, api_key=API_KEY):
        genai.configure(api_key=api_key, transport="rest")

        self.model_name = GEMINI_MODEL
        self.calculator = Calculator()
        self.cx_connector = CXConnector()

        print(self.calculator.tools)

        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
            tools=[self.calculator.tools],
        )

    def call_agent(self, prompt: str) -> str:
        chat = self.model.start_chat()
        response = chat.send_message(prompt)

        print("🤖 Agent response:", response)

        while True:
            function_calls = []
            for candidate in response.candidates:
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
                    # if hasattr(self.calculator, tool_name):
                    #     tool_func = getattr(self.calculator, tool_name)
                    # elif hasattr(self.cx_connector, tool_name):
                    #     tool_func = getattr(self.cx_connector, tool_name)
                    # else:
                    #     raise AttributeError(f"Tool {tool_name} not found")
                    # Directly execute the tool from the calculator instance
                    tool_func = getattr(self.calculator, tool_name)
                    tool_result = tool_func(**args)
                    result_str = str(tool_result)
                except (AttributeError, TypeError) as e:
                    result_str = f"Error: Tool {tool_name} not found or not callable."
                except Exception as e:
                    result_str = f"Error: {str(e)}"

                tool_responses.append(
                    {
                        "function_response": {
                            "name": tool_name,
                            "response": {"result": result_str},
                        }
                    }
                )

            # Send tool responses back to Gemini
            response = chat.send_message(
                {
                    "role": "function",
                    "parts": tool_responses,
                }
            )
            print("🤖 Tool responses:", tool_responses)

    def __call__(self, prompt: str) -> str:
        return self.call_agent(prompt)

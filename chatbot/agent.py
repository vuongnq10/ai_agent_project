# agent.py
import google.generativeai as genai
from chatbot.tool_server import ToolServer
import os

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")


class Agent:
    def __init__(self, api_key=API_KEY):
        # Init Gemini
        genai.configure(api_key=api_key, transport="rest")

        self.model_name = GEMINI_MODEL

        # Init tools
        self.tool_server = ToolServer()

        # Get tool configurations
        tools_config = self.tool_server.get_tools_config()

        # Configure model with tools
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
            tools=tools_config,
            tool_config={"function_calling_config": "ANY"},
        )

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        return self.tool_server.execute_tool(tool_name, **kwargs)

    def call_agent(self, prompt: str) -> str:
        chat = self.model.start_chat()
        response = chat.send_message(prompt)

        print("Initial response:", response)

        function_calls = []
        # results = []

        while True:
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason

            if finish_reason == "STOP":
                print("✅ Final result:", candidate.content.parts[0].text)
                return candidate.content.parts[0].text

            for candidate in response.candidates:
                if not candidate.content.parts:
                    continue

                for part in candidate.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        try:

                            tool_name = part.function_call.name
                            args = part.function_call.args

                            result = self.execute_tool(tool_name, **args)

                            response = chat.send_message(
                                content=genai.types.Content(
                                    role="tool",
                                    parts=[
                                        genai.types.Part(
                                            function_response={
                                                "name": tool_name,
                                                "response": result,
                                            }
                                        )
                                    ],
                                )
                            )

                        except Exception as e:
                            function_calls.append(f"{tool_name} (failed)")
                            # results.append(f"Error: {str(e)}")

    def call_agent_old(self, prompt: str) -> str:
        try:
            enhanced_prompt = prompt

            print(enhanced_prompt)

            # Start chat and get response
            chat = self.model.start_chat()
            response = chat.send_message(enhanced_prompt)

            print(response)

            if not response.candidates:
                return "No response was generated."

            function_calls = []
            results = []

            # Process each part of the response
            for candidate in response.candidates:
                if not candidate.content.parts:
                    continue

                for part in candidate.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        try:

                            tool_name = part.function_call.name
                            args = part.function_call.args

                            result = self.execute_tool(tool_name, **args)

                            args_str = ", ".join(f"{k}={v}" for k, v in args.items())

                            function_calls.append(f"{tool_name}({args_str})")
                            results.append(str(result))

                        except Exception as e:
                            function_calls.append(f"{tool_name} (failed)")
                            results.append(f"Error: {str(e)}")

            # Format the response
            if not function_calls:
                return "No tools were called. Try rephrasing your request."

            steps = "\n".join(
                [
                    f"\n {i+1}. Called {call} → {result}"
                    for i, (call, result) in enumerate(zip(function_calls, results))
                ]
            )

            return f"""Tool Execution Steps: 
                    {steps}"""

        except Exception as e:
            return f"Error processing request: {str(e)}\nContext: Ensure the request is clear and specific."

    def __call__(self, prompt: str) -> str:
        return self.call_agent(prompt)

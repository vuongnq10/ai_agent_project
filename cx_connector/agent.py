import os
from .cx_connector import CXConnector
from .tool_server import ToolServer
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
# tool_server = ToolServer()


class Agent:
    def __init__(self, api_key=GEMINI_API_KEY):
        # Init Gemini
        genai.configure(api_key=api_key, transport="rest")

        self.model_name = "gemini-1.5-flash"

        # Init tools
        self.tool_server = ToolServer()

        # Get tool configurations
        # tools_config = self.tool_server.mcp.tools.values()

        # Configure model with tools
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
            tools=self.tool_server.get_tools_config(),
        )

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """
        Execute a specific tool with given arguments

        Args:
            tool_name (str): Name of the tool to execute
            **kwargs: Arguments to pass to the tool

        Returns:
            str: Result from the tool execution
        """
        return self.tool_server.execute_tool(tool_name, **kwargs)

    def call_agent(self, prompt: str) -> str:
        """
        Process the user prompt using Gemini and execute appropriate tool functions

        Args:
            prompt (str): The user's input query

        Returns:
            str: The response from processing the prompt
        """
        try:
            # Add context to the prompt about using both tools
            # enhanced_prompt = f"""This task must be completed in exactly two steps:
            #     1. First call gen_random to generate the number: {prompt}
            #     2. Then use the result from gen_random as input to answer_random to format it nicely
            #     This is a two-step process - both tools must be used in sequence for a complete response.
            #     DO NOT skip either step - the task is incomplete without both steps."""
            enhanced_prompt = f"""Generate a random number between 25 to 75, if the answer is greater than 60, generate the string with number"""

            # Start chat and get response
            chat = self.model.start_chat()
            response = chat.send_message(enhanced_prompt)

            print("-" * 20)
            print(f"Debug - Response: {response}")  # Debug line
            print("-" * 20)

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
                        print(
                            f"Debug - Found function call: {part.function_call.name}"
                        )  # Debug line
                        try:
                            # Extract function call details
                            tool_name = part.function_call.name
                            args = part.function_call.args

                            # Execute the tool
                            result = self.execute_tool(tool_name, **args)

                            # Format arguments nicely
                            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
                            # Store details for final response
                            function_calls.append(f"{tool_name}({args_str})")
                            results.append(str(result))

                            # If this was gen_random, automatically chain to answer_random
                            if tool_name == "gen_random":
                                format_result = self.execute_tool(
                                    "answer_random", random=result
                                )
                                function_calls.append(f"answer_random(random={result})")
                                results.append(str(format_result))
                        except Exception as e:
                            function_calls.append(f"{tool_name} (failed)")
                            results.append(f"Error: {str(e)}")

            # Format the response
            if not function_calls:
                return "No tools were called. Try rephrasing your request."

            steps = "\n".join(
                [
                    f"{i+1}. Called {call} → {result}"
                    for i, (call, result) in enumerate(zip(function_calls, results))
                ]
            )

            return f"""Tool Execution Steps:
                    {steps}"""

        except Exception as e:
            return f"Error processing request: {str(e)}\nContext: Ensure the request is clear and specific."

    def __call__(self, prompt: str) -> str:
        """
        Make the agent callable directly

        Args:
            prompt (str): The user's input query

        Returns:
            str: The response from the agent
        """
        return self.call_agent(prompt)

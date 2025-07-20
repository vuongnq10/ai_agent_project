# tool_server.py
from dataclasses import dataclass
from typing import List, Any, Callable
import random


@dataclass
class Tool:
    name: str
    func: Callable
    description: str
    input_params: dict


class ToolServer:
    def __init__(self):
        self.tools = {}
        self.register_tools()

    @staticmethod
    def gen_random(start=0, end=100):
        return random.randint(int(start), int(end))

    @staticmethod
    def answer_random(number: int):
        return f"Generated random number: {number}"

    @staticmethod
    def sum_numbers(a: int, b: int) -> int:
        """Sum two numbers."""
        return a + b

    def register_tools(self):
        self.register_tool(
            "gen_random",
            self.gen_random,
            "Generate a random number between start and end (inclusive).",
            {"start": "integer", "end": "integer"},
        )
        self.register_tool(
            "sum_numbers",
            self.sum_numbers,
            "Sum two integers.",
            {"a": "integer", "b": "integer"},
        )
        self.register_tool(
            "answer_random",
            self.answer_random,
            "Format the answer for a random number.",
            {"random": "integer"},
        )

    def register_tool(
        self, name: str, func: Callable, description: str, input_params: dict
    ):
        self.tools[name] = Tool(name, func, description, input_params)

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool directly by name with given arguments"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")

        tool = self.tools[tool_name]
        return tool.func(**kwargs)

    def get_tools_config(self):
        """Get tool configurations in format compatible with Gemini"""
        function_declarations = []
        for tool in self.tools.values():
            properties = {}
            for param_name, param_type in tool.input_params.items():
                properties[param_name] = {
                    "type": param_type,
                    "description": f"The {param_name} parameter for {tool.name}",
                }

            function_declarations.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "OBJECT",
                        "properties": properties,
                        "required": list(tool.input_params.keys()),
                    },
                }
            )

        return [{"function_declarations": function_declarations}]

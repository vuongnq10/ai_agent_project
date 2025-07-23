# tool_server.py
from dataclasses import dataclass
from typing import Callable
import random


@dataclass
class Tool:
    name: str
    func: Callable
    description: str
    input_params: dict


class Calculator:
    def __init__(self):
        self.tools = {}
        self.register_tools()

    def register_tools(self):
        self.register_tool(
            "gen_random",
            Calculator.gen_random,
            "Generate a random number between start and end (inclusive).",
            {
                "start": "The starting number for the random range.",
                "end": "The ending number for the random range.",
            },
        )
        self.register_tool(
            "sum_numbers",
            Calculator.sum_numbers,
            "Sum two integers.",
            {"a": "The first number to add.", "b": "The second number to add."},
        )

    def register_tool(
        self, name: str, func: Callable, description: str, input_params: dict
    ):
        self.tools[name] = Tool(name, func, description, input_params)

    @staticmethod
    def gen_random(start=0, end=100):
        return random.randint(int(start), int(end))

    @staticmethod
    def sum_numbers(a: int, b: int) -> int:
        """Sum two numbers."""
        return a + b

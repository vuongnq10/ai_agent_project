import random
from google.generativeai.types import Tool, FunctionDeclaration


class Calculator:
    def __init__(self):
        self.tools = self.register_tools()

    @staticmethod
    def gen_random(start=0, end=100):
        return random.randint(int(start), int(end))

    @staticmethod
    def sum_numbers(a: int, b: int) -> int:
        """Sum two numbers."""
        return a + b

    @staticmethod
    def sum_even_numbers(numbers: list) -> int:
        """Sum the even numbers from a list of numbers."""
        return sum(num for num in numbers if num % 2 == 0)

    def register_tools(self):
        return Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="gen_random",
                    description="Generate a random integer between start and end.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "start": {
                                "type": "integer",
                                "description": "Start of range",
                            },
                            "end": {"type": "integer", "description": "End of range"},
                        },
                        "required": ["start", "end"],
                    },
                ),
                FunctionDeclaration(
                    name="sum_numbers",
                    description="Sum two integers.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "a": {"type": "integer", "description": "First number"},
                            "b": {"type": "integer", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                ),
                FunctionDeclaration(
                    name="sum_even_numbers",
                    description="Sum the even numbers from a list of numbers.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "numbers": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "List of numbers to sum if they are even",
                            }
                        },
                        "required": ["numbers"],
                    },
                ),
            ]
        )

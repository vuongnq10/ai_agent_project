import random


class Calculator:
    def __init__(self):
        self.tools = {}
        self.register_tools()

    def register_tools(self):
        self.tools = {
            "function_declarations": [
                {
                    "name": "add",
                    "description": "Add two integers.",
                    "function": self.add,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "integer", "description": "First number"},
                            "b": {"type": "integer", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                },
                {
                    "name": "multiply",
                    "description": "Multiply two integers.",
                    "function": self.multiply,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "integer", "description": "First number"},
                            "b": {"type": "integer", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                },
                {
                    "name": "get_random_number",
                    "description": "Generate a random number between start and end (inclusive).",
                    "function": self.get_random_number,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start": {
                                "type": "integer",
                                "default": 0,
                                "description": "Start of range",
                            },
                            "end": {
                                "type": "integer",
                                "default": 10,
                                "description": "End of range",
                            },
                        },
                        "required": [],
                    },
                },
            ]
        }

    def add(self, a: int, b: int) -> int:
        """Returns the sum of two numbers."""

        print(f"Adding {a} and {b}")

        return a + b

    def multiply(self, a: int, b: int) -> int:
        """Returns the product of two numbers."""

        print(f"Multiplying {a} and {b}")

        return a * b

    def get_random_number(self, start=0, end=10) -> int:
        """Generate a random number between start and end (inclusive)."""
        random_number = random.randint(start, end)

        print(f"Generated random number: {random_number}")

        return random_number

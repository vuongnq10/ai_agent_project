import random
from google.genai.types import Tool, FunctionDeclaration


class Calculator:
    def __init__(self):
        self.tools = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="random",
                    description="Generate a random number between start and end",
                    parameters={
                        "type": "object",
                        "properties": {
                            "start": {
                                "type": "integer",
                                "default": 1,
                                "description": "Start of the range",
                            },
                            "end": {
                                "type": "integer",
                                "default": 100,
                                "description": "End of the range",
                            },
                        },
                        "required": ["start", "end"],
                    },
                ),
                FunctionDeclaration(
                    name="add",
                    description="Add two numbers",
                    parameters={
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                ),
                FunctionDeclaration(
                    name="subtract",
                    description="Subtract second number from first number",
                    parameters={
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                ),
            ]
        )

    def random(self, start=1, end=100):
        value = random.randint(start, end)

        print(f"Generated random number: {value}")

        return {"result": value}

    def add(self, a, b):

        print(f"Adding {a} and {b}")

        return {"result": a + b}

    def subtract(self, a, b):

        print(f"Subtracting {b} from {a}")

        return {"result": a - b}

import random
from google.genai.types import Tool, FunctionDeclaration


class Calculator:
    def __init__(self):
        self.tools = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="gen_random",
                    description="Return a random integer between 1 and n",
                    parameters={
                        "type": "object",
                        "properties": {
                            "start": {
                                "type": "integer",
                                "description": "Start of range for random number",
                            },
                            "end": {
                                "type": "integer",
                                "description": "End of range for random number",
                            },
                        },
                        "required": ["start", "end"],
                    },
                ),
                FunctionDeclaration(
                    name="sum_numbers",
                    description="Return the sum of two numbers a and b",
                    parameters={
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                ),
            ],
        )

    def gen_random(self, start=0, end=100):

        print(f"🔢 Generating random number between {start} and {end}")

        return {"result": random.randint(int(start), int(end))}

    def sum_numbers(self, a: int, b: int):

        print(f"➕ Summing numbers: {a} + {b}")

        return {"result": a + b}

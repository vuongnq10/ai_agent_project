import random
from google.generativeai.types import Tool, FunctionDeclaration


class Calculator:
    def __init__(self):
        self.tools = Tool(
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
            ]
        )

    @staticmethod
    def gen_random(start=0, end=100):

        print(f"🔢 Generating random number between {start} and {end}")

        return random.randint(int(start), int(end))

    @staticmethod
    def sum_numbers(a: int, b: int) -> int:

        print(f"➕ Summing numbers: {a} + {b}")

        return a + b

    # def register_tools(self):
    #     return Tool(
    #         function_declarations=[
    #             FunctionDeclaration(
    #                 name="gen_random",
    #                 description="Generate a random integer between start and end.",
    #                 parameters={
    #                     "type": "object",
    #                     "properties": {
    #                         "start": {
    #                             "type": "integer",
    #                             "description": "Start of range",
    #                         },
    #                         "end": {"type": "integer", "description": "End of range"},
    #                     },
    #                     "required": ["start", "end"],
    #                 },
    #             ),
    #             FunctionDeclaration(
    #                 name="sum_numbers",
    #                 description="Sum two integers.",
    #                 parameters={
    #                     "type": "object",
    #                     "properties": {
    #                         "a": {"type": "integer", "description": "First number"},
    #                         "b": {"type": "integer", "description": "Second number"},
    #                     },
    #                     "required": ["a", "b"],
    #                 },
    #             ),
    #         ]
    #     )

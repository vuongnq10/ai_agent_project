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

        return random.randint(int(start), int(end))

    def sum_numbers(self, a: int, b: int) -> int:

        print(f"➕ Summing numbers: {a} + {b}")

        return a + b


# import ccxt
# import random
# from google.genai.types import Tool, FunctionDeclaration

# # binance = ccxt.binance({})


# class Calculator:
#     def __init__(self):
#         self.tools = Tool(
#             function_declarations=[
#                 FunctionDeclaration(
#                     name="gen_random",
#                     description="Generate a random integer between start and end.",
#                     parameters={
#                         "type": "object",
#                         "properties": {
#                             "start": {
#                                 "type": "integer",
#                                 "description": "Start of range",
#                             },
#                             "end": {"type": "integer", "description": "End of range"},
#                         },
#                         "required": ["start", "end"],
#                     },
#                 ),
#                 FunctionDeclaration(
#                     name="sum_numbers",
#                     description="Sum two integers.",
#                     parameters={
#                         "type": "object",
#                         "properties": {
#                             "a": {"type": "integer", "description": "First number"},
#                             "b": {"type": "integer", "description": "Second number"},
#                         },
#                         "required": ["a", "b"],
#                     },
#                 ),
#                 # FunctionDeclaration(
#                 #     name="get_ticker",
#                 #     description="Fetch ticker data for a given symbol and timeframe.",
#                 #     parameters={
#                 #         "type": "object",
#                 #         "properties": {
#                 #             "symbol": {
#                 #                 "type": "string",
#                 #                 "description": "The trading pair symbol (e.g., 'SOL/USDT').",
#                 #             },
#                 #             "timeframe": {
#                 #                 "type": "string",
#                 #                 "description": "The timeframe for the OHLCV data (e.g., '1h', '30m').",
#                 #             },
#                 #         },
#                 #         "required": ["symbol", "timeframe"],
#                 #     },
#                 # ),
#             ]
#         )

#     @staticmethod
#     def gen_random(start=0, end=100):

#         print(f"🔢 Generating random number between {start} and {end}")

#         return random.randint(int(start), int(end))

#     @staticmethod
#     def sum_numbers(a: int, b: int) -> int:

#         print(f"➕ Summing numbers: {a} + {b}")

#         return a + b

#     # @staticmethod
#     # def get_ticker(symbol: str, timeframe: str):
#     #     """
#     #     Mock function to simulate fetching ticker data.
#     #     In a real implementation, this would fetch data from an exchange.
#     #     """
#     #     print(f"📈 Fetching ticker data for {symbol} at {timeframe} timeframe")
#     #     ohlcv = binance.fetch_ohlcv(symbol, timeframe)

#     #     print(f"📈 Fetched OHLCV data for {symbol} at {timeframe} timeframe: {ohlcv}")
#     #     return ohlcv

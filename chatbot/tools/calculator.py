import random

import ccxt
import pandas as pd
from google.genai.types import Tool, FunctionDeclaration

binance = ccxt.binance({})


class Calculator:
    def __init__(self):
        self.tools = Tool(
            function_declarations=[
                # FunctionDeclaration(
                #     name="gen_random",
                #     description="Return a random integer between 1 and n",
                #     parameters={
                #         "type": "object",
                #         "properties": {
                #             "start": {
                #                 "type": "integer",
                #                 "description": "Start of range for random number",
                #             },
                #             "end": {
                #                 "type": "integer",
                #                 "description": "End of range for random number",
                #             },
                #         },
                #         "required": ["start", "end"],
                #     },
                # ),
                # FunctionDeclaration(
                #     name="sum_numbers",
                #     description="Return the sum of two numbers a and b",
                #     parameters={
                #         "type": "object",
                #         "properties": {
                #             "a": {"type": "number", "description": "First number"},
                #             "b": {"type": "number", "description": "Second number"},
                #         },
                #         "required": ["a", "b"],
                #     },
                # ),
                # FunctionDeclaration(
                #     name="get_ticker",
                #     description="Fetch ticker data for a given symbol and timeframe.",
                #     parameters={
                #         "type": "object",
                #         "properties": {
                #             "symbol": {
                #                 "type": "string",
                #                 "description": "The trading pair symbol (e.g., 'SOL/USDT').",
                #             },
                #             "timeframe": {
                #                 "type": "string",
                #                 "description": "The timeframe for the OHLCV data (e.g., '1h', '30m').",
                #                 "default": "1h",
                #             },
                #         },
                #         "required": ["symbol", "timeframe"],
                #     },
                # ),
                # FunctionDeclaration(
                #     name="calculate_market_structure",
                #     description="Calculate market structure based on recent candles.",
                #     parameters={
                #         "type": "object",
                #         "properties": {
                #             "candles": {
                #                 "type": "array",
                #                 "items": {
                #                     "type": "object",
                #                     "properties": {
                #                         "timestamp": {"type": "string"},
                #                         "open": {"type": "number"},
                #                         "high": {"type": "number"},
                #                         "low": {"type": "number"},
                #                         "close": {"type": "number"},
                #                         "volume": {"type": "number"},
                #                     },
                #                 },
                #             }
                #         },
                #         "required": ["candles"],
                #     },
                # ),
                FunctionDeclaration(
                    name="calculate_market_structure",
                    description="Calculate market structure based on recent OHLCV data.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The trading pair symbol (e.g., 'SOL/USDT').",
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "The timeframe for the OHLCV data (e.g., '1h', '30m').",
                                "default": "1h",
                            },
                        },
                        "required": ["symbol", "timeframe"],
                    },
                ),
            ],
        )

    # def gen_random(self, start=0, end=100):

    #     print(f"🔢 Generating random number between {start} and {end}")

    #     return {"result": random.randint(int(start), int(end))}

    # def sum_numbers(self, a: int, b: int):

    #     print(f"➕ Summing numbers: {a} + {b}")

    #     return {"result": a + b}

    def get_ticker(self, symbol: str, timeframe="1h"):
        print(f"📈 Fetching ticker data for {symbol} at {timeframe} timeframe")
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=100)

        print(f"📈 Fetched OHLCV data for {symbol} at {timeframe} timeframe: {ohlcv}")
        return {"result": ohlcv}

    # def calculate_market_structure(self, candles: list):
    def calculate_market_structure(self, symbol: str, timeframe="1h"):
        candles = binance.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(
            candles,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        swing_highs = []
        swing_lows = []

        for i in range(1, len(df) - 1):
            if (
                df["high"].iloc[i] > df["high"].iloc[i - 1]
                and df["high"].iloc[i] > df["high"].iloc[i + 1]
            ):
                swing_highs.append({"price": df["high"].iloc[i], "index": i})
            if (
                df["low"].iloc[i] < df["low"].iloc[i - 1]
                and df["low"].iloc[i] < df["low"].iloc[i + 1]
            ):
                swing_lows.append({"price": df["low"].iloc[i], "index": i})

        structure = "UNDEFINED"
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            recent_highs = swing_highs[:2]
            recent_lows = swing_lows[:2]
            higher_highs = recent_highs[0]["price"] > recent_highs[1]["price"]
            higher_lows = recent_lows[0]["price"] > recent_lows[1]["price"]
            if higher_highs and higher_lows:
                structure = "BULLISH_TREND"
            elif not higher_highs and not higher_lows:
                structure = "BEARISH_TREND"
            elif higher_highs and not higher_lows:
                structure = "BULLISH_BREAKOUT"
            elif not higher_highs and higher_lows:
                structure = "BEARISH_BREAKOUT"
            else:
                structure = "CONSOLIDATION"

        return {
            "result": {
                "structure": structure,
                "swingHighs": swing_highs,
                "swingLows": swing_lows,
            }
        }

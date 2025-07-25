import ccxt
import pandas as pd
from google.generativeai.types import Tool, FunctionDeclaration

binance = ccxt.binance({})


class CXConnector:
    def __init__(self):
        self.tools = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="get_ticker",
                    description="Fetch ticker data for a given symbol and timeframe.",
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
                            },
                        },
                        "required": ["symbol", "timeframe"],
                    },
                ),
                FunctionDeclaration(
                    name="save_trade_setup",
                    description="Saves a trade setup with symbol, order type, entry price, stop loss, and take profit.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The trading pair symbol (e.g., 'SOL/USDT').",
                            },
                            "order_type": {
                                "type": "string",
                                "description": "Type of order (e.g., 'buy', 'sell').",
                            },
                            "entry": {
                                "type": "number",
                                "description": "Entry price for the trade.",
                            },
                            "stop_loss": {
                                "type": "number",
                                "description": "Stop loss price for the trade.",
                            },
                            "take_profit": {
                                "type": "number",
                                "description": "Take profit price for the trade.",
                            },
                        },
                        "required": [
                            "symbol",
                            "order_type",
                            "entry",
                            "stop_loss",
                            "take_profit",
                        ],
                    },
                ),
                FunctionDeclaration(
                    name="calculate_market_structure",
                    description="Calculates market structure based on recent OHLCV data.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "candles": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "timestamp": {"type": "string"},
                                        "open": {"type": "number"},
                                        "high": {"type": "number"},
                                        "low": {"type": "number"},
                                        "close": {"type": "number"},
                                        "volume": {"type": "number"},
                                    },
                                },
                            },
                        },
                        "required": ["candles"],
                    },
                ),
            ]
        )

    def get_ticker(self, symbol: str, timeframe: str):
        print(f"📈 Fetching ticker data for {symbol} at {timeframe} timeframe")
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=100)

        print(f"📈 Fetched OHLCV data for {symbol} at {timeframe} timeframe: {ohlcv}")
        return ohlcv

    @staticmethod
    def calculate_market_structure(candles: list):
        df = pd.DataFrame(
            candles[-50:],
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
            "structure": structure,
            "swingHighs": swing_highs,
            "swingLows": swing_lows,
        }

    @staticmethod
    def save_trade_setup(
        symbol: str,
        order_type: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
    ):
        try:
            string = f"Placing {order_type} order of {symbol} at price {entry}, stop loss at {stop_loss}, take profit at {take_profit}"

            print(string)
            # asyncio.run(telegram_bot(string))

            return {"status": "success", "message": string}
        except Exception as e:
            return {"status": "error", "message": str(e)}

import ccxt
import pandas as pd
from google.genai.types import Tool, FunctionDeclaration

binance = ccxt.binance({})


class CXConnector:
    def __init__(self):
        self.tools = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="smc_analysis",
                    description="Perform Smart Money Concept analysis on the given symbol and timeframe.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The trading pair symbol (e.g., 'SOL/USDT').",
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "The timeframe for the analysis (e.g., '1h', '30m').",
                                "default": "1h",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of candles to fetch for analysis.",
                                "default": 100,
                            },
                        },
                        "required": ["symbol", "timeframe"],
                    },
                ),
                FunctionDeclaration(
                    name="save_trade_setup",
                    description="Save a trade setup with entry, stop loss, and take profit.",
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
            ],
        )

    def get_ticker(self, symbol: str, timeframe="1h"):
        print(f"📈 Fetching ticker data for {symbol} at {timeframe} timeframe")
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=100)

        print(f"📈 Fetched OHLCV data for {symbol} at {timeframe} timeframe: {ohlcv}")
        return {"result": ohlcv}

    def smc_analysis(self, symbol: str, timeframe="1h", limit=100):
        candles = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        current_price = candles[-1][4]

        booinger_bands = self.boolinger_bands(candles)
        sma = self.sma(candles)
        market_structure = self.calculate_market_structure(candles)
        # rsi = self.rsi(candles)

        return {
            "result": {
                "current_price": current_price,
                "bollinger_bands": booinger_bands,
                "sma": sma,
                "market_structure": market_structure,
                # "rsi": rsi,
            }
        }

    def calculate_market_structure(self, candles):
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
            "structure": structure,
            "swingHighs": swing_highs,
            "swingLows": swing_lows,
        }

    def boolinger_bands(self, candles, period=20):
        df = pd.DataFrame(
            candles[-period:],
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        df["sma"] = df["close"].rolling(window=period).mean()
        df["std"] = df["close"].rolling(window=period).std()
        df["upper_band"] = df["sma"] + (2 * df["std"])
        df["lower_band"] = df["sma"] - (2 * df["std"])

        return {
            "upper_band": df["upper_band"].iloc[-1],
            "lower_band": df["lower_band"].iloc[-1],
            "sma": df["sma"].iloc[-1],
        }

    def sma(self, candles, period=20):
        df = pd.DataFrame(
            candles[-period:],
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        df["sma"] = df["close"].rolling(window=period).mean()

        return df["sma"].iloc[-1]

    def rsi(self, candles, period=14):
        df = pd.DataFrame(
            candles[-period:],
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]

    def save_trade_setup(
        self,
        symbol: str,
        order_type: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
    ):
        try:
            string = f"Placing {order_type} order of {symbol} at price {entry}, stop loss at {stop_loss}, take profit at {take_profit}"

            print(string)

            return {"result": string}
        except Exception as e:
            return {"status": "error", "message": str(e)}

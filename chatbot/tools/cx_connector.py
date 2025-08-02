import ccxt
import pandas as pd
from google.genai.types import Tool, FunctionDeclaration

from chatbot.binance_connector.binance import BinanceConnector

binance = ccxt.binance({})
binance_connector = BinanceConnector()


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
                                "description": "The trading pair symbol (e.g., 'SOLUSDT').",
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
                                "description": "The trading pair symbol (e.g., 'SOLUSDT').",
                            },
                            "side": {
                                "type": "string",
                                "description": "Type of order (e.g., 'BUY', 'SELL').",
                            },
                            "entry": {
                                "type": "number",
                                "description": "Entry price for the trade. ",
                            },
                            # "stop_loss": {
                            #     "type": "string",
                            #     "description": "Stop loss price for the trade. String representation of a float.",
                            # },
                            # "take_profit": {
                            #     "type": "string",
                            #     "description": "Take profit price for the trade. String representation of a float.",
                            # },
                        },
                        "required": [
                            "symbol",
                            "side",
                            "entry",
                            # "stop_loss",
                            # "take_profit",
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
        self.current_price = candles[-1][4]

        booinger_bands = self.bollinger_bands(candles)
        sma = self.sma(candles)
        market_structure = self.calculate_market_structure(candles)
        rsi = self.rsi(candles)

        return {
            "result": {
                "bollinger_bands": booinger_bands,
                "sma": sma,
                "market_structure": market_structure,
                "rsi": rsi,
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

    def bollinger_bands(self, candles, period=20, multiplier=2):
        data_frame = pd.DataFrame(
            candles[-period:],
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )

        data_frame["sma"] = data_frame["close"].rolling(window=period).mean()
        data_frame["std"] = data_frame["close"].rolling(window=period).std()

        data_frame["upper_band"] = data_frame["sma"] + (multiplier * data_frame["std"])
        data_frame["lower_band"] = data_frame["sma"] - (multiplier * data_frame["std"])

        return {
            "upper_band": data_frame["upper_band"].iloc[-1],
            "lower_band": data_frame["lower_band"].iloc[-1],
            "sma": data_frame["sma"].iloc[-1],
        }

    def sma(self, candles, period=20):
        data_framge = pd.DataFrame(
            candles[-period:],
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        data_framge["sma"] = data_framge["close"].rolling(window=period).mean()

        return data_framge["sma"].iloc[-1]

    def rsi(self, candles, period=14):
        data_frame = pd.DataFrame(
            candles[-period:],
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )

        delta = data_frame["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]

    def save_trade_setup(
        self,
        symbol: str,
        side: str,
        entry: float,
    ):
        try:
            response = binance_connector.create_orders(
                symbol=symbol,
                side=side,
                price=entry,
                current_price=self.current_price,
            )

            return {"result": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

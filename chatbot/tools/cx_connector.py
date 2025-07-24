import ccxt
from google.generativeai.types import Tool, FunctionDeclaration

binance = ccxt.binance({})


class CXConnector:
    def __init__(self):
        self.tools = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="ticker_ohlcv",
                    description="Fetches the live ticker price and history for a given symbol and timeframe.",
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
            ]
        )

    @staticmethod
    def ticker_ohlcv(symbol: str, timeframe: str):
        """
        Fetches the ticker price for a given symbol and timeframe.

        :param symbol: The trading pair symbol (e.g., 'SOL/USDT').
        :param timeframe: The timeframe for the OHLCV data (e.g., '1h', '30m').
        :return: A list of dictionaries containing the OHLCV data.
        """
        ohlcv = binance.fetch_ohlcv(symbol, timeframe)

        print(f"📈 Fetched OHLCV data for {symbol} at {timeframe} timeframe")

        return ohlcv

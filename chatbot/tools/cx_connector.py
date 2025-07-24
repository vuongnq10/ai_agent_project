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

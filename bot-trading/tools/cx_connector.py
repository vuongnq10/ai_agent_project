from google.genai.types import Tool, FunctionDeclaration

from connectors.binance_v2 import BinanceConnector
from services.smc_service import SmcService

binance_connector = BinanceConnector()
_smc_service = SmcService()


class CXConnector:
    def __init__(self):
        self.current_price = None
        self.tools = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="create_order",
                    description="Save a 20 leverage trade setup with entry, stop loss, and take profit.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The trading pair symbol (e.g., 'SOLUSDT').",
                            },
                            "current_price": {
                                "type": "number",
                                "description": "Current market price for the symbol.",
                            },
                            "side": {
                                "type": "string",
                                "description": "Type of order (e.g., 'BUY', 'SELL').",
                            },
                            "entry": {
                                "type": "number",
                                "description": "Entry price for the trade. ",
                            },
                            "stop_loss": {
                                "type": "string",
                                "description": "Stop loss price for the trade. String representation of a float.",
                            },
                            "take_profit": {
                                "type": "string",
                                "description": "Take profit price for the trade. String representation of a float.",
                            },
                        },
                        "required": [
                            "symbol",
                            "side",
                            "entry",
                            "take_profit",
                            "stop_loss",
                        ],
                    },
                ),
            ],
        )

    def smc_analysis(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> dict:
        return _smc_service.smc_analysis(symbol, timeframe, limit)

    def create_order(
        self,
        symbol: str,
        current_price: float,
        side: str,
        entry: float,
        take_profit: float,
        stop_loss: float,
    ):
        if current_price is None:
            return {"status": "error", "message": "current_price not set"}
        try:
            response = binance_connector.create_orders(
                symbol=symbol,
                side=side,
                order_price=entry,
                current_price=current_price,
                take_profit=take_profit,
                stop_loss=stop_loss,
            )
            return {"result": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_ticker(self, symbol: str, timeframe: str = "1h"):
        candles = _smc_service.fetch_candles(symbol, timeframe, limit=100)
        return {"result": candles}

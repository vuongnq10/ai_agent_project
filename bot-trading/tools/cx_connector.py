from connectors.binance_v2 import BinanceConnector
from services.smc_service import SmcService

binance_connector = BinanceConnector()
_smc_service = SmcService()


class CXConnector:
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

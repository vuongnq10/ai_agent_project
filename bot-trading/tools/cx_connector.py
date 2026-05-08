from connectors.binance_v2 import BinanceConnector
from services.candle_service import CandleService
from services.smc_service import SmcService
from services.wyckoff_service import WyckoffService

binance_connector = BinanceConnector()
_candle_service = CandleService()
_smc_service = SmcService()
_wyckoff_service = WyckoffService()


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
        candles = _candle_service.fetch_candles(symbol, timeframe, limit=100)
        return {"result": candles}

    def wyckoff_analysis(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> dict:
        return _wyckoff_service.wyckoff_analysis(symbol, timeframe, limit)

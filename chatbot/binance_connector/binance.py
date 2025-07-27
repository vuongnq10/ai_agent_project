# https://github.com/binance/binance-connector-python/tree/master
# https://github.com/binance/binance-connector-python/tree/master/clients/derivatives_trading_usds_futures
# https://github.com/binance/binance-connector-python/blob/master/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/rest_api.py
import os
from binance.cm_futures import CMFutures

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL")


class BinanceConnector:
    def __init__(self):
        self.balance = 0

        self.client = CMFutures(
            key=BINANCE_API_KEY,
            secret=BINANCE_SECRET_KEY,
            base_url=BINANCE_BASE_URL,
        )
        # self.get_balance()

    def get_balance(self):
        account_info = self.client.balance(recvWindow=6000)

        return account_info

    def create_orders(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
    ):
        params = [
            {
                "symbol": "BTCUSD_PERP",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": "0.001",
                "timeInForce": "GTC",
                "price": "60000.1",
            }
        ]
        order = self.client.new_batch_order()
        return order

    def fetch_ohlcv(self, symbol, timeframe, limit=100):
        candles = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)
        return candles

    def ticker_ohlcv(self, symbol, timeframe="1h", limit=100):
        binance = self.client

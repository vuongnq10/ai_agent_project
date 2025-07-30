# https://github.com/binance/binance-connector-python/tree/master
# https://github.com/binance/binance-connector-python/tree/master/clients/derivatives_trading_usds_futures
# https://github.com/binance/binance-connector-python/blob/master/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/rest_api.py
import os

from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
    DerivativesTradingUsdsFutures,
)
from binance_sdk_derivatives_trading_usds_futures.rest_api.models import (
    ExchangeInformationResponse,
)
from binance_sdk_derivatives_trading_usds_futures.rest_api.models import (
    PlaceMultipleOrdersBatchOrdersParameterInner,
)

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL")

configuration = ConfigurationRestAPI(
    api_key=BINANCE_API_KEY,
    api_secret=BINANCE_SECRET_KEY,
    base_path=BINANCE_BASE_URL,
)


class BinanceConnector:
    def __init__(self):
        self.balance = 0
        self.positions = []

        self.client = DerivativesTradingUsdsFutures(config_rest_api=configuration)
        self.get_balance()

    def get_balance(self):
        response = self.client.rest_api.account_information_v3()

        value = response.data().to_dict()

        assets = value.get("assets", [])
        for asset in assets:
            if asset.get("asset") == "USDT":
                self.balance = float(asset.get("walletBalance", 0))
                break

        self.positions = value.get("positions", [])

    def create_orders(
        self,
        # symbol: str,
        # side: str,
        # order_type: str,
        # quantity: str,
        # price: str = None,
    ):
        try:
            orders = [
                {
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "LIMIT",
                    "price": "100000",
                    "quantity": "1",
                    "timeInForce": "GTC",
                },
                {
                    "symbol": "BTCUSDT",
                    "side": "SELL",
                    "type": "TAKE_PROFIT_MARKET",
                    "stopPrice": "120000",
                    "closePosition": "true",
                },
                {
                    "symbol": "BTCUSDT",
                    "side": "SELL",
                    "type": "STOP_MARKET",
                    "stopPrice": "90000",
                    "closePosition": "true",
                },
            ]

            response = self.client.rest_api.place_multiple_orders(orders)

            data = response.data()

            return [item.to_dict() for item in data]
        except Exception as e:
            print(f"Error creating orders: {e}")
            return None

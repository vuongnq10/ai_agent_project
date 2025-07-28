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
        orders = self.client.rest_api.place_multiple_orders(params)

        return orders.data().to_dict()

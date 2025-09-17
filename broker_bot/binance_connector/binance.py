# https://github.com/binance/binance-connector-python/tree/master
# https://github.com/binance/binance-connector-python/tree/master/clients/derivatives_trading_usds_futures
# https://github.com/binance/binance-connector-python/blob/master/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/rest_api.py
import os
import asyncio

from broker_bot.telegram.telegram import telegram_bot

from binance_common.configuration import ConfigurationRestAPI
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
    DerivativesTradingUsdsFutures,
)

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL")

configuration = ConfigurationRestAPI(
    api_key=BINANCE_API_KEY,
    api_secret=BINANCE_SECRET_KEY,
    # base_path=BINANCE_BASE_URL,
)

# LEVERAGE = 20
# ORDER_AMOUNT = 50
# EXPECTED_PROFIT = 2
# EXPECTED_STOP_LOSS = 2

LEVERAGE = 20
ORDER_AMOUNT = 20
EXPECTED_PROFIT = 0.35
EXPECTED_STOP_LOSS = 0.25


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

        print("Wallet Balance:", self.balance)

        self.positions = value.get("positions", [])

    def match_precision(self, value, reference_str):
        decimals = len(reference_str.split(".")[1]) if "." in reference_str else 0
        return round(value, decimals)

    def create_orders(
        self,
        symbol: str,
        side: str,
        order_price: float,
        current_price: float,
        take_profit: float,
        stop_loss: float,
    ):
        if (side == "BUY" and order_price > current_price) or (
            side == "SELL" and order_price < current_price
        ):
            asyncio.run(
                telegram_bot(
                    f"Order price {order_price} for {symbol} is not valid for current price {current_price} for side {side}"
                )
            )
            return "Failed"

        try:
            symbol_config = self.get_exchange_info(symbol)
            filter = symbol_config.get("filters", [])
            price_filter = next(
                (item for item in filter if item["filterType"] == "PRICE_FILTER"), None
            )
            lot_size_filter = next(
                (item for item in filter if item["filterType"] == "LOT_SIZE"), None
            )

            quantity = self.match_precision(
                (float(ORDER_AMOUNT) * LEVERAGE) / order_price,
                lot_size_filter["stepSize"],
            )
            real_price = self.match_precision(order_price, price_filter["tickSize"])
            profit_price = 0.1
            stop_price = 0.1

            if side == "BUY":
                temp_profit = order_price * (
                    1 + float(EXPECTED_PROFIT) / float(LEVERAGE)
                )
                temp_stop = order_price * (
                    1 - float(EXPECTED_STOP_LOSS) / float(LEVERAGE)
                )

                profit_price = self.match_precision(
                    temp_profit, price_filter["tickSize"]
                )
                stop_price = self.match_precision(temp_stop, price_filter["tickSize"])
            elif side == "SELL":
                temp_profit = order_price * (
                    1 - float(EXPECTED_PROFIT) / float(LEVERAGE)
                )
                temp_stop = order_price * (
                    1 + float(EXPECTED_STOP_LOSS) / float(LEVERAGE)
                )

                profit_price = self.match_precision(
                    temp_profit, price_filter["tickSize"]
                )
                stop_price = self.match_precision(temp_stop, price_filter["tickSize"])

            orders = [
                {
                    "symbol": symbol,
                    "side": side,
                    "type": "LIMIT",
                    "price": str(real_price),
                    "quantity": str(quantity),
                    "timeInForce": "GTC",
                },
                {
                    "symbol": symbol,
                    "side": "BUY" if side == "SELL" else "SELL",
                    "type": "TAKE_PROFIT_MARKET",
                    "stopPrice": take_profit,  # str(profit_price),
                    "closePosition": "true",
                },
                {
                    "symbol": symbol,
                    "side": "BUY" if side == "SELL" else "SELL",
                    "type": "STOP_MARKET",
                    "stopPrice": stop_loss, # str(stop_price),
                    "closePosition": "true",
                },
            ]

            print(f"Creating orders: {orders}")

            response = self.client.rest_api.place_multiple_orders(orders)

            data = response.data()
            result = [item.to_dict() for item in data]

            asyncio.run(telegram_bot(result))

            asyncio.run(
                telegram_bot(
                    f"""
                    🛒 Create an order for {symbol}  
                    ➡️ Side: {side}  
                    🏷️ Order Type: {side}  
                    💰 Current Price: ${current_price}  
                    🎯 Order Price: ${real_price}  
                    📦 Quantity: {quantity}  
                    📈 Profit Price: ${profit_price}  
                    🛑 Stop Price: ${stop_price}  
                    """
                )
            )

            return "success"
        except Exception as e:
            asyncio.run(
                telegram_bot(
                    f"""
                    Error creating orders for {symbol} with side {side} and price {order_price}:
                    {str(e)}
                """
                )
            )
            print(f"Error creating orders: {e}")
            return None

    def get_exchange_info(self, symbol: str = None):

        response = self.client.rest_api.exchange_information()
        data = response.data().to_dict()

        symbols = data.get("symbols", [])

        obj_symbols = next((item for item in symbols if item["symbol"] == symbol), None)

        return obj_symbols

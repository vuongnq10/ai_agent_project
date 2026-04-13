# https://github.com/binance/binance-connector-python
# Uses binance-connector-python (UMFutures) instead of binance_sdk_derivatives_trading_usds_futures
import asyncio

from connectors.telegram import telegram_bot
from binance.um_futures import UMFutures
import config

BINANCE_API_KEY = config.BINANCE_API_KEY
BINANCE_SECRET_KEY = config.BINANCE_SECRET_KEY
BINANCE_BASE_URL = config.BINANCE_BASE_URL

LEVERAGE = 15
ORDER_AMOUNT = 8
EXPECTED_PROFIT = 0.40
EXPECTED_STOP_LOSS = 0.30


class BinanceConnector:
    def __init__(self):
        self.balance = 0
        self.positions = []

        self.client = UMFutures(
            key=BINANCE_API_KEY,
            secret=BINANCE_SECRET_KEY,
            base_url=(
                BINANCE_BASE_URL if BINANCE_BASE_URL else "https://fapi.binance.com"
            ),
        )

    def get_balance(self):
        value = self.client.account()

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

    def create_orders_default(
        self,
        symbol: str,
        side: str,
        order_price: float,
        current_price: float,
    ):
        if (side == "BUY" and order_price > current_price) or (
            side == "SELL" and order_price < current_price
        ):
            asyncio.create_task(
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
                    "stopPrice": str(profit_price),
                    "closePosition": "true",
                    "timeInForce": "GTC",
                    "firstTrigger": "PLACE_ORDER",
                    "firstDrivenOn": "PARTIALLY_FILLED_OR_FILLED",
                },
                {
                    "symbol": symbol,
                    "side": "BUY" if side == "SELL" else "SELL",
                    "type": "STOP_MARKET",
                    "stopPrice": str(stop_price),
                    "closePosition": "true",
                    "timeInForce": "GTC",
                    "firstTrigger": "PLACE_ORDER",
                    "firstDrivenOn": "PARTIALLY_FILLED_OR_FILLED",
                },
            ]

            print(f"Creating orders: {orders}")

            asyncio.create_task(
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
            asyncio.create_task(
                telegram_bot(
                    f"""
                    Error creating orders for {symbol} with side {side} and price {order_price}:
                    {str(e)}
                """
                )
            )
            print(f"Error creating orders: {e}")
            return None

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
            asyncio.create_task(
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
            tp_price = self.match_precision(
                float(take_profit), price_filter["tickSize"]
            )
            sl_price = self.match_precision(float(stop_loss), price_filter["tickSize"])

            close_side = "BUY" if side == "SELL" else "SELL"

            print(
                f"Placing LIMIT order: {symbol} {side} qty={quantity} price={real_price}"
            )
            limit_resp = self.client.new_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                price=str(real_price),
                quantity=str(quantity),
                timeInForce="GTC",
            )

            algo_orders = [
                {
                    "symbol": symbol,
                    "side": close_side,
                    "type": "TAKE_PROFIT_MARKET",
                    "triggerPrice": str(tp_price),
                    "quantity": str(quantity),
                    "reduceOnly": "true",
                    "timeInForce": "GTC",
                    "algoType": "CONDITIONAL",
                },
                {
                    "symbol": symbol,
                    "side": close_side,
                    "type": "STOP_MARKET",
                    "triggerPrice": str(sl_price),
                    "quantity": str(quantity),
                    "reduceOnly": "true",
                    "timeInForce": "GTC",
                    "algoType": "CONDITIONAL",
                },
            ]

            print(f"Placing algo orders (TP + SL): {algo_orders}")
            algo_results = [
                self.client.sign_request("POST", "/fapi/v1/algoOrder", order)
                for order in algo_orders
            ]

            result = [limit_resp, *algo_results]

            asyncio.create_task(telegram_bot(result))

            return result
        except Exception as e:
            asyncio.create_task(
                telegram_bot(
                    f"""
                    Error creating orders for {symbol} with side {side} and price {order_price}:
                    {str(e)}
                """
                )
            )
            print(f"Error creating orders: {e}")
            return None

    def set_leverage(self, symbol: str, leverage: int):
        try:
            data = self.client.change_leverage(symbol=symbol, leverage=leverage)
            print(f"Leverage set for {symbol}: {data}")
            return data
        except Exception as e:
            print(f"Error setting leverage for {symbol}: {e}")
            return None

    def get_exchange_info(self, symbol: str = None):
        data = self.client.exchange_info()

        symbols = data.get("symbols", [])

        obj_symbols = next((item for item in symbols if item["symbol"] == symbol), None)

        return obj_symbols

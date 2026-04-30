# https://github.com/binance/binance-connector-python
# Uses binance-connector-python (UMFutures) instead of binance_sdk_derivatives_trading_usds_futures
import asyncio

from connectors.telegram import telegram_bot
from binance.um_futures import UMFutures
import config

BINANCE_API_KEY = config.BINANCE_API_KEY
BINANCE_SECRET_KEY = config.BINANCE_SECRET_KEY
BINANCE_BASE_URL = config.BINANCE_BASE_URL

LEVERAGE = 10
ORDER_AMOUNT = 14
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

    def create_orders(
        self,
        symbol: str,
        side: str,
        order_price: float,
        current_price: float,
        take_profit: float,
        stop_loss: float,
    ):
        """
        Place a 3-leg bracket order on Binance USDS Futures:
          1. LIMIT entry          — via POST /fapi/v1/order  (client.new_order)
          2. TAKE_PROFIT_MARKET   — via POST /fapi/v1/algoOrder (client.sign_request)
          3. STOP_MARKET          — via POST /fapi/v1/algoOrder (client.sign_request)

        NOTE: As of December 2025, STOP_MARKET and TAKE_PROFIT_MARKET orders must be
        submitted through /fapi/v1/algoOrder — using /fapi/v1/order returns error -4120.
        TP and SL do NOT cancel each other automatically (true OTOCO is not available
        via REST alone); a WebSocket user-data-stream listener would be required for that.

        Returns a list of 3 API responses on success, or None on exception.
        """
        if (side == "BUY" and order_price > current_price) or (
            side == "SELL" and order_price < current_price
        ):
            asyncio.create_task(
                telegram_bot(
                    f"Invalid order price {order_price} for {symbol}: "
                    f"current price is {current_price}, side is {side}"
                )
            )
            return None

        try:
            symbol_config = self.get_exchange_info(symbol)
            filters = symbol_config.get("filters", [])
            price_filter = next(
                (f for f in filters if f["filterType"] == "PRICE_FILTER"), None
            )
            lot_size_filter = next(
                (f for f in filters if f["filterType"] == "LOT_SIZE"), None
            )

            quantity = self.match_precision(
                (float(ORDER_AMOUNT) * LEVERAGE) / order_price,
                lot_size_filter["stepSize"],
            )
            real_entry = self.match_precision(order_price, price_filter["tickSize"])
            real_tp = self.match_precision(float(take_profit), price_filter["tickSize"])
            real_sl = self.match_precision(float(stop_loss), price_filter["tickSize"])

            close_side = "BUY" if side == "SELL" else "SELL"

            # --- 1. LIMIT entry order ---
            print(
                f"Placing LIMIT order: {symbol} {side} qty={quantity} price={real_entry}"
            )
            limit_resp = self.client.new_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                price=str(real_entry),
                quantity=str(quantity),
                timeInForce="GTC",
            )

            # --- 2 & 3. Algo orders: TP and SL ---
            # Both use algoType=CONDITIONAL and triggerPrice (not stopPrice).
            # workingType=CONTRACT_PRICE means the trigger is compared against the
            # last traded price rather than the mark price.
            tp_params = {
                "symbol": symbol,
                "side": close_side,
                "type": "TAKE_PROFIT_MARKET",
                "algoType": "CONDITIONAL",
                "triggerPrice": str(real_tp),
                "quantity": str(quantity),
                "reduceOnly": "true",
                "workingType": "CONTRACT_PRICE",
                "priceProtect": "TRUE",
                "timeInForce": "GTC",
            }
            sl_params = {
                "symbol": symbol,
                "side": close_side,
                "type": "STOP_MARKET",
                "algoType": "CONDITIONAL",
                "triggerPrice": str(real_sl),
                "quantity": str(quantity),
                "reduceOnly": "true",
                "workingType": "CONTRACT_PRICE",
                "priceProtect": "TRUE",
                "timeInForce": "GTC",
            }

            print(f"Placing TP algo order: {tp_params}")
            tp_resp = self.client.sign_request("POST", "/fapi/v1/algoOrder", tp_params)

            print(f"Placing SL algo order: {sl_params}")
            sl_resp = self.client.sign_request("POST", "/fapi/v1/algoOrder", sl_params)

            result = [limit_resp, tp_resp, sl_resp]

            asyncio.create_task(
                telegram_bot(
                    f"Order placed — {symbol}\n"
                    f"Side: {side}\n"
                    f"Entry (LIMIT): {real_entry}\n"
                    f"Quantity: {quantity}\n"
                    f"Take Profit: {real_tp}\n"
                    f"Stop Loss: {real_sl}"
                )
            )

            return result

        except Exception as e:
            asyncio.create_task(
                telegram_bot(
                    f"Error creating orders for {symbol} | side={side} | "
                    f"entry={order_price}: {str(e)}"
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

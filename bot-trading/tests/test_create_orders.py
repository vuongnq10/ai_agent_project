# Run: cd /Users/nguyen.quoc.vuong/Documents/ai_agent_project/bot-trading && source venv/bin/activate && python tests/test_create_orders.py

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# from src.binance_connector.binance import BinanceConnector

from src.binance_connector.binance_v2 import BinanceConnector

# Constant test inputs
SYMBOL = "TIAUSDT"
SIDE = "BUY"
ORDER_PRICE = 0.28
CURRENT_PRICE = 0.29
TAKE_PROFIT = 0.3
STOP_LOSS = 0.27


async def main():
    connector = BinanceConnector()

    print(f"Testing create_orders with:")
    print(f"  symbol={SYMBOL}, side={SIDE}")
    print(f"  order_price={ORDER_PRICE}, current_price={CURRENT_PRICE}")
    print(f"  take_profit={TAKE_PROFIT}, stop_loss={STOP_LOSS}")

    result = connector.create_orders(
        symbol=SYMBOL,
        side=SIDE,
        order_price=ORDER_PRICE,
        current_price=CURRENT_PRICE,
        take_profit=TAKE_PROFIT,
        stop_loss=STOP_LOSS,
    )

    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

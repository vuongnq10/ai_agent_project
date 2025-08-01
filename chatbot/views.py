# 1. N8N
# 2. Langchain
# 3. LLMs

import asyncio
from django.http import JsonResponse
from chatbot.tools.agent import Agent
from chatbot.telegram.telegram import telegram_bot
from chatbot.binance_connector.binance import BinanceConnector

agent = Agent()
binance_connector = BinanceConnector()


def chat(request):
    user_message = request.GET.get("query")

    print("User message:", user_message)

    response = agent(user_message)
    return JsonResponse({"success": True, "message": response})


# def ticker_data(request):
#     symbol = request.GET.get("symbol", "SOL/USDT")
#     timeframe = request.GET.get("timeframe", "1h")

#     try:
#         ohlcv_data = cx_conntector.ticker_ohlcv(symbol, timeframe)

#         return JsonResponse(
#             {
#                 "success": True,
#                 "symbol": symbol,
#                 "timeframe": timeframe,
#                 "data": ohlcv_data,
#             }
#         )
#     except Exception as e:
#         return JsonResponse({"success": False, "error": str(e)})


def telegram_notify(request):
    message = request.GET.get("message", "No message provided")
    more = request.GET.get("more", "")

    try:
        response = asyncio.run(telegram_bot(message, more))
        return JsonResponse({"success": True, "response": response})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def test_binance(request):
    # params = binance_connector.create_orders(
    #     symbol="SOLUSDT", side="BUY", quantity="0.1", price="20.0"
    # )
    # message = request.GET.get("coin")
    # params = binance_connector.get_exchange_info(symbol=message)
    params = binance_connector.create_orders("BNBUSDT", "BUY", 0.3140)

    return JsonResponse({"success": True, "data": params})

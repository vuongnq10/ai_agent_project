# 1. N8N
# 2. Langchain
# 3. LLMs
# 4. LangGraph

import asyncio
import time
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from chatbot.tools.agent import Agent
from chatbot.telegram.telegram import telegram_bot
from chatbot.binance_connector.binance import BinanceConnector
from chatbot.tools.cx_connector import CXConnector

agent = Agent()
binance_connector = BinanceConnector()
cx_connector = CXConnector()


def chat(request):
    user_message = request.GET.get("query")

    print("User message:", user_message)

    response = agent(user_message)
    return JsonResponse({"success": True, "message": response})


def chat_stream(request):
    user_message = request.GET.get("query")

    def event_stream():
        for char in user_message:
            yield f"data: {char}\n\n"
            time.sleep(0.005) # Delay for 300ms

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


def telegram_notify(request):
    message = request.GET.get("message", "No message provided")
    more = [
        {
            "symbol": "SUIUSDT",
            "side": "SELL",
            "type": "LIMIT",
            "price": "3.4684",
            "quantity": "14.4",
            "timeInForce": "GTC",
        },
        {
            "symbol": "SUIUSDT",
            "side": "BUY",
            "type": "TAKE_PROFIT_MARKET",
            "stopPrice": "3.347006",
            "closePosition": "true",
        },
        {
            "symbol": "SUIUSDT",
            "side": "BUY",
            "type": "STOP_MARKET",
            "stopPrice": "3.589794",
            "closePosition": "true",
        },
    ]

    try:
        response = asyncio.run(telegram_bot(message, more))
        return JsonResponse({"success": True, "response": response})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def test_binance(request):
    coin = request.GET.get("coin", "No coin provided")
    ticker = cx_connector.smc_analysis(coin, "1h")
    # bollinger_bands = cx_connector.bollinger_bands(ticker["result"])

    return JsonResponse({"success": True, "data": ticker})

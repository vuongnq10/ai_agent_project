# 1. N8N
# 2. Langchain
# 3. LLMs

from django.http import JsonResponse
import os
from chatbot.tools.agent import Agent
from chatbot.tools.cx_connector import CXConnector

GEMINI_MODEL = "gemini-1.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
agent = Agent()
cx_conntector = CXConnector()


def chat(request):
    user_message = request.GET.get("query")

    response = agent(user_message)  # Using the callable instance
    return JsonResponse({"success": True, "message": response})


def ticker_data(request):
    symbol = request.GET.get("symbol", "SOL/USDT")
    timeframe = request.GET.get("timeframe", "1h")

    try:
        ohlcv_data = cx_conntector.ticker_ohlcv(symbol, timeframe)

        return JsonResponse(
            {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data": ohlcv_data,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

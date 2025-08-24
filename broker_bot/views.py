# 1. N8N
# 2. Langchain
# 3. LLMs
# 4. LangGraph
# 5. langgraph with condition like AI gives a response to ask if user wants to continue
# 6. https://phoenix.arize.com/

import asyncio
import time
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from broker_bot.tools.agent import Agent
from broker_bot.telegram.telegram import telegram_bot

agent = Agent()


def chat(request):
    user_message = request.GET.get("query")

    print("User message:", user_message)

    message = agent(user_message)

    return JsonResponse({"success": True, "data": message})


# def chat(request):
#     user_message = request.GET.get("query")

#     print("User message:", user_message)

#     def event_stream():
#         try:
#             for chunk in agent(user_message):
#                 yield f"data: {chunk}\n\n"

#         except Exception as e:
#             print(f"Error in streaming: {e}")
#             yield f"data: Error: {str(e)}\n\n"

#     return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


def chat_stream(request):
    user_message = request.GET.get("query")

    def event_stream():
        for char in user_message:
            yield f"data: {char}\n\n"
            time.sleep(0.005)  # Delay for 300ms

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

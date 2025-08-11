from django.http import JsonResponse

from chat_app.bot.bot import ChatBot

chat_bot = ChatBot()


def chat(request):
    session_id = request.GET.get("session_id", "default")
    user_message = request.GET.get("query")

    print("User message:", user_message)

    reply_message = chat_bot.bot_response(user_message)

    return JsonResponse({"ok": True, "data": reply_message})

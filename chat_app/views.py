from django.http import JsonResponse
from chat_app.bot.bot import ChatBot
from google.genai.types import Content, Part
from django.views.decorators.csrf import csrf_exempt

chat_bot = ChatBot()

@csrf_exempt
def chat(request):
    if request.method == 'POST':
        user_message = request.POST.get("query")
    else:
        return JsonResponse({"ok": False, "error": "Only POST requests are allowed"}, status=405)

    print("User message:", user_message)
    print("Session key:", request.session.session_key)
    print("Session items before:", dict(request.session.items()))

    # Retrieve chat history from session
    chat_history_data = request.session.get("chat_history", [])

    # Convert chat history data (list of dicts) back to Content objects
    chat_history = []

    for item in chat_history_data:
        role = item["role"]
        parts = [Part.from_text(text=p["text"]) for p in item["parts"]]
        chat_history.append(Content(role=role, parts=parts))

    # reply_message = chat_bot.bot_response(user_message, chat_history)

    # Append the new user message and bot reply to the history
    chat_history.append(Content(role="user", parts=[Part.from_text(text=user_message)]))
    chat_history.append(
        Content(role="model", parts=[Part.from_text(text="reply_message")])
    )

    print("Updated chat history:", chat_history)
    print("Session items after:", dict(request.session.items()))

    # Store updated chat history in session (convert Content objects to dicts for session storage)
    request.session["chat_history"] = [
        {"role": c.role, "parts": [{"text": p.text} for p in c.parts if p.text]}
        for c in chat_history
    ]
    request.session.modified = True

    return JsonResponse({"ok": True, "data": "reply_message"})

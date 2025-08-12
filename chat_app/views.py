from django.http import JsonResponse
from chat_app.bot.bot import ChatBot
from google.genai.types import Content, Part

chat_bot = ChatBot()


def chat(request):
    session_id = request.GET.get("session_id", "default")
    user_message = request.GET.get("query")

    print("User message:", user_message)

    # Retrieve chat history from session
    chat_history_data = request.session.get(f"chat_history_{session_id}", [])

    # Convert chat history data (list of dicts) back to Content objects
    chat_history = []

    print("Chat history data:", chat_history_data)

    for item in chat_history_data:
        role = item["role"]
        parts = [Part.from_text(text=p["text"]) for p in item["parts"]]
        chat_history.append(Content(role=role, parts=parts))

    reply_message = chat_bot.bot_response(user_message, chat_history)

    # Append the new user message and bot reply to the history
    chat_history.append(Content(role="user", parts=[Part.from_text(text=user_message)]))
    chat_history.append(
        Content(role="model", parts=[Part.from_text(text=reply_message)])
    )

    # Store updated chat history in session (convert Content objects to dicts for session storage)
    request.session[f"chat_history_{session_id}"] = [
        {"role": c.role, "parts": [{"text": p.text} for p in c.parts if p.text]}
        for c in chat_history
    ]
    request.session.modified = True

    return JsonResponse({"ok": True, "data": reply_message})

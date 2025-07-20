# 1. N8N
# 2. Langchain
# 3. LLMs

from django.http import JsonResponse
import os
from chatbot.agent import Agent

GEMINI_MODEL = "gemini-1.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
agent = Agent()


def chat(request):
    user_message = request.GET.get("query")

    response = agent(user_message)  # Using the callable instance
    return JsonResponse({"success": True, "message": response})

from django.urls import path
from .views import chat_gemini, chat_openai

urlpatterns = [
    path("", chat_gemini, name="chat"),
    path("/open_ai", chat_openai, name="open_ai"),
]

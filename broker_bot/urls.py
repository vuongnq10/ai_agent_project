from django.urls import path
from .views import chat, telegram_notify, chat_stream, test_cx

urlpatterns = [
    path("", chat, name="chat"),
    # path("/ticker_data", ticker_data, name="ticker_data"),
    path("/chat_stream", chat_stream, name="chat_stream"),
    path("/telegram_notify", telegram_notify, name="telegram_notify"),
    path("/test_cx", test_cx, name="test_cx"),
]

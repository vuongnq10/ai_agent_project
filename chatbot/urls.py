from django.urls import path
from .views import chat, telegram_notify, test_binance

urlpatterns = [
    path("", chat, name="chat"),
    # path("/ticker_data", ticker_data, name="ticker_data"),
    path("/telegram_notify", telegram_notify, name="telegram_notify"),
    path("/test_binance", test_binance, name="test_binance"),
]

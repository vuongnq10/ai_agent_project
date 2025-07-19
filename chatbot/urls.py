from django.urls import path
from .views import chat

urlpatterns = [
    path("", chat, name="chat"),
    # path("/ticker_data", ticker_data, name="ticker_data"),
]

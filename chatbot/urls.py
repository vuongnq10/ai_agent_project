from django.urls import path
from .views import chat, hello_world_api

urlpatterns = [
    path("", chat, name="chat"),
    path("/hello_world", hello_world_api, name="hello_world_api"),
]

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/game/chat/<str:room_name>/', consumers.AsyncChatConsumer),
    path('ws/game/game/<str:room_name>/', consumers.GameConsumer),
]
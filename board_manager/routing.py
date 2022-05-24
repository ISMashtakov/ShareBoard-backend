from django.urls import path

from .consumers import BoardEditorConsumer

websocket_urlpatterns = [
    path('boards/<boards_id>/<access_token>/', BoardEditorConsumer.as_asgi()),
]

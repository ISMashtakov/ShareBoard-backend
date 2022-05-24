from django.urls import path

from .consumers import FileEditorConsumer

websocket_urlpatterns = [
    path('files/<file_id>/<access_token>/', FileEditorConsumer.as_asgi()),
]

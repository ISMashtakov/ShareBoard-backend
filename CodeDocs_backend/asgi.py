"""
ASGI config for CodeDocs_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

import file_manager.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CodeDocs_backend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket":     URLRouter(
            file_manager.routing.websocket_urlpatterns
    ),
})

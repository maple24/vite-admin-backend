"""
ASGI config for backendviteadmin project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendviteadmin.settings')
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from .auth import JWTAuthMiddlewareStack

import ws.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # Just HTTP for now. (We can add other protocols later.)
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStack(URLRouter(ws.routing.websocket_urlpatterns))
        ),
    }
)

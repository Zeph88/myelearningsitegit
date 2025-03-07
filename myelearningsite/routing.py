from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from elearningapp.routing import websocket_urlpatterns
from django.core.asgi import get_asgi_application
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myelearningsite.settings')
django.setup()

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    "http": get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})

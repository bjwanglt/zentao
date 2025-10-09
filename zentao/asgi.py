"""
ASGI config for zentao project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.sessions import SessionMiddlewareStack

from channels.routing import ProtocolTypeRouter, URLRouter
from . import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentao.settings')

# application = get_asgi_application()

# application = ProtocolTypeRouter(
#     dict(
#         http=get_asgi_application(),  # 自动寻找urls.py
#         websocket=URLRouter(routing.websocket_urlpatterns)
#     )
# )


application = ProtocolTypeRouter(
    dict(
        http=get_asgi_application(),
        websocket=SessionMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        ),
    )
)

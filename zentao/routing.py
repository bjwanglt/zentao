from django.urls import re_path

from web.views.handler_websocket import MsgConsummer
from web.views.handle_assgin_msg import AssginMsgHandler

websocket_urlpatterns = [
    re_path(r'ws/(?P<group>\w+)/$', AssginMsgHandler.as_asgi())
]

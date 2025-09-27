# filepath: core/routing.py
from django.urls import re_path
from . import consumers
from core import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<lawyer_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]
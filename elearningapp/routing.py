from django.urls import re_path, path

from . import consumers

# NOTE USE OF ws/ to separate out our ws URIs, like rest use of api/
websocket_urlpatterns = [
    re_path(r'ws/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/feedback/(?P<room_name>\w+)/$', consumers.FeedbackConsumer.as_asgi()),
    re_path(r'ws/connect/(?P<user_id>\w+)/$', consumers.ConnectConsumer.as_asgi()),
]

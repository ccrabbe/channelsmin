from django.conf.urls import url
from ..consumers import ChannelsMinConsumer
from otree.channels.routing import websocket_routes


websocket_routes += [
    url(r'^channelsmin/(?P<params>[\w,]+)/$',
        ChannelsMinConsumer),
]

# Uncomment this line to print websocket_routes for troubleshooting
# print("websocket_routes="+str(websocket_routes))

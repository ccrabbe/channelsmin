from channels.routing import route
from channelsmin.consumers import ws_add as cm_ws_add, ws_disconnect as cm_ws_disconnect, ws_receive as cm_ws_receive
from otree.channels.routing import channel_routing

channel_routing += [
    route('websocket.connect', cm_ws_add,
          path=r'^/channelsmin/(?P<params>[\w,]+)/$'),
    route('websocket.receive', cm_ws_receive,
          path=r'^/channelsmin/(?P<params>[\w,]+)/$'),
    route('websocket.disconnect', cm_ws_disconnect,
          path=r'^/channelsmin/(?P<params>[\w,]+)/$'),
]

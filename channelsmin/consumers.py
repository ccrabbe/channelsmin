# from channels import Group
import json
from django.db import transaction
import otree.channels.utils as channel_utils
from django.conf import settings
from channels.generic.websocket import (
    JsonWebsocketConsumer, WebsocketConsumer)
ALWAYS_UNRESTRICTED = 'ALWAYS_UNRESTRICTED'
UNRESTRICTED_IN_DEMO_MODE = 'UNRESTRICTED_IN_DEMO_MODE'

import logging
logger = logging.getLogger(__name__)

from otree.common_internal import (
    get_models_module
)
from asgiref.sync import async_to_sync


#  Copied from otree.channels.consumers.py - where Chris asks not to directly subclass but rather copy this over
#  It provides a basic implementation of a consumer with several functions to be defined by the implementing class
class _OTreeJsonWebsocketConsumer(JsonWebsocketConsumer):
    '''
    THIS IS NOT PUBLIC API.
    Third party apps should not subclass this.
    Either copy this class into your code,
    or subclass directly from JsonWebsocketConsumer,
    '''

    def group_send_channel(self, type: str, groups=None, **event):
        print('in group_send_channel')
        for group in (groups or self.groups):
            channel_utils.sync_group_send(group, {'type': type, **event})
            #print('call_args', channel_utils.sync_group_send.call_args)
            #assert channel_utils.sync_group_send.call_args

    def clean_kwargs(self, **kwargs):
        '''
        subclasses should override if the route receives a comma-separated params arg.
        otherwise, this just passes the route kwargs as is (usually there is just one).
        The output of this method is passed to self.group_name(), self.post_connect,
        and self.pre_disconnect, so within each class, all 3 of those methods must
        accept the same args (or at least take a **kwargs wildcard, if the args aren't used)
        '''
        return kwargs

    def group_name(self, **kwargs):
        raise NotImplementedError()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleaned_kwargs = self.clean_kwargs(**self.scope['url_route']['kwargs'])
        self.groups = self.connection_groups()

    def connection_groups(self, **kwargs):
        group_name = self.group_name(**self.cleaned_kwargs)
        return [group_name]

    unrestricted_when = ''

    # there is no login_required for channels
    # so we need to make our own
    # https://github.com/django/channels/issues/1241
    def connect(self):
        # need to accept no matter what, so we can at least send
        # an error message
        self.accept()

        AUTH_LEVEL = settings.AUTH_LEVEL

        auth_required = (
            (not self.unrestricted_when) and AUTH_LEVEL
            or
            self.unrestricted_when == UNRESTRICTED_IN_DEMO_MODE and AUTH_LEVEL == 'STUDY'
        )

        if auth_required and not self.scope['user'].is_staff:
            msg = 'rejected un-authenticated access to websocket'
            logger.warning(msg)
            # it's good to send an explanation so we understand e.g.
            # test failures
            self.send_json({'unauthenticated_websocket': msg})
            return
        else:
            self.post_connect(**self.cleaned_kwargs)

    def post_connect(self, **kwargs):
        pass

    def disconnect(self, message, **kwargs):
        self.pre_disconnect(**self.cleaned_kwargs)

    def pre_disconnect(self, **kwargs):
        pass

    def receive_json(self, content, **etc):
        self.post_receive_json(content, **self.cleaned_kwargs)

    def post_receive_json(self, content, **kwargs):
        pass


# Extend the copied-over _OTreeJsonWebsocketConsumer by implementing:
#   clean_kwargs - parses the arguments passed in the channel URL
#   group_name - constructs a unique group name for the channel_layer
#   post_connect - adds player to a channel_layer and performs any actions needed upon connecting a client
#   pre_disconnect - performs any actions needed after a player disconnects, and removes them from the channel_layer
#   post_receive_json - performs the actions required when receiving a message
#
#   You also need one more function to parse messages of each "type" you expect sent over the channels (in this case:  channelsmin_message()
class ChannelsMinConsumer(_OTreeJsonWebsocketConsumer):

    unrestricted_when = ALWAYS_UNRESTRICTED

    # parse the parameters passed in the websockets URL and return a dict with name: value pairs
    def clean_kwargs(self, params):
        page, group_id, player_id, session_code = params.split(',')
        return {
            'page': page,
            'group_id': int(group_id),
            'session_code': session_code,
            'player_id': int(player_id)
        }

    # return a unique group_name for the channel_layer so that each oTree group gets its own channel_layer
    def group_name(self, page, group_id, session_code, player_id):
        return "channelsmin_session-" + str(session_code) + "_group-" + str(group_id)

    # parse messages of type channelsmin_message
    def channelsmin_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))

    # perform actions neccesary to add a subject to their group's channel_layer.  In our case, if a group has already ended
    # we need to send them a message saying that, so that they can go to the end page too
    def post_connect(self, page, group_id, session_code, player_id):
        # add them to the channel_layer
        self.room_group_name = self.group_name(page, group_id, session_code, player_id)
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        # need to check to see if someone in the group has already chosen to move on - if so, send the done message upon joining
        with transaction.atomic():
            models_module = get_models_module('channelsmin')
            group_object = models_module.Group.objects.get(id=group_id)

            if page == 'finished' and group_object.firstpage_done:
                print("inside ws_add, checking to see if group's first page is done.  firstpage_done=" + str(
                    group_object.firstpage_done))

                # prepare the message to send
                reply = {
                    'type': 'channelsmin_message',
                    'message': 'done',
                }

                # send the message
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    reply
                )

    # perform any actions necessary before removing a subject from the channel_layer.  In our case there's nothing to do but
    # discard them from the channel layer
    def pre_disconnect(self, page, group_id, session_code, player_id):

        # remove the player from their channel_layer
        self.room_group_name = self.group_name(page, group_id, session_code, player_id)
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )


    # handle non-connect and non-disconnect messages.  We only expect one message, one with the 'message' of 'done'
    # When we receive that, update the group object's "firstpage_done" field to True, save it to the db, and send a
    # message to the rest of the channel_layer telling them we're done
    def post_receive_json(self, content, page, group_id, session_code, player_id):

        message_type = content['message']

        models_module = get_models_module('channelsmin')
        print("ws_receive called, page=" + str(page) + ", message_type=" + str(message_type))
        if page == 'finished':
            # check the message_type - if we're doing more complicated things later different messages can mean different things
            # ... this helps me organize
            if message_type == 'done':
                # make sure to do all these operations at once so that there's less chance of threading issues
                with transaction.atomic():
                    # set the group as being finished, so we can automatically forward anybody who joins the page late
                    group_object = models_module.Group.objects.get(id=group_id)
                    group_object.firstpage_done = True
                    group_object.save()

                    # prepare the message to send
                    reply = {
                        'type': 'channelsmin_type',
                        'message': 'done'
                    }

                    # send the message
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        reply
                    )
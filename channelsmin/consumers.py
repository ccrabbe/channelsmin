from channels import Group
import json
from django.db import transaction
from otree.common_internal import (
    get_models_module
)


# Generate some unique group id for this group in this subsession
def get_group_name(group_id, sid):
    return "channelsmin_session-" + str(sid) + "_group-" + str(group_id)


# called when a message is received over the channel
def ws_receive(message, params):
    # ASGI WebSocket packet-received and send-packet message types
    # both have a "text" key for their textual data.
    print("ws_receive called.")
    data = json.loads(message['text'])
    message_type = data['type']

    page,group_id, player_id, session_code = params.split(',')
    player_id = int(player_id)
    group_id = int(group_id)

    models_module = get_models_module('channelsmin')
    print("ws_receive called, page="+str(page)+", message_type="+str(message_type))
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

                reply = {
                    'type': 'done',
                }
                # send the click to the other players in the group
                Group(get_group_name(group_id, session_code)).send(
                    {'text': json.dumps(reply)}
                )


# called when a player leaves the channel
def ws_disconnect(message, params):
    print("ws_disconnect called.")

    # remove the player from the group
    page,group_id, player_id, session_code = params.split(',')
    Group(get_group_name(group_id, session_code)).discard(message.reply_channel)


# called when a player joins the channel
def ws_add(message, params):
    print("ws_add called. params = " + params)
    page,group_id, player_id, session_code = params.split(',')
    player_id = int(player_id)
    group_id = int(group_id)

    # add them to the channels group
    group = Group(get_group_name(group_id, session_code))
    group.add(message.reply_channel)

    # need to check to see if someone in the group has already chosen to move on - if so, send the done message upon joining
    with transaction.atomic():
        models_module = get_models_module('channelsmin')
        group_object = models_module.Group.objects.get(id=group_id)

        if page=='finished' and group_object.firstpage_done:
            print("inside ws_add, checking to see if group's first page is done.  firstpage_done=" + str(group_object.firstpage_done))

            reply = {
                'type': 'done',
            }
            message.reply_channel.send(
                {'text': json.dumps(reply)}
            )


import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
import channels.auth


class ChannelConsumer(AsyncWebsocketConsumer):
    '''
    when a client send a message, the message will be received by consumer first and then broadcast to channel layer, and then to other group memebers 
    '''
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name
        # 127.0.0.1 will be considered as anonymous, use localhost
        if self.scope['user'].is_anonymous:
            return AnonymousUser()
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        '''
        Called when receiving messages from group channel
        '''
        text_data_json = json.loads(text_data)
        purpose = text_data_json.get("purpose", None)
        message = text_data_json.get("message", "No message found!")

        # Send events over the channel layer (broadcast)
        if purpose == 'chat': 
            hanlder_func = "chat_message"
        elif purpose == 'log':
            hanlder_func = "log_message"
        else:
            hanlder_func = "unexpected_message"
            
        await self.channel_layer.group_send(
            self.room_group_name, 
            {
                "type": hanlder_func,
                # "room_id": room_id,
                "username": self.scope["user"].username,
                "message": message
            }
        )

    # handling function to receive events and turn them into websockets 
    async def chat_message(self, event):
        '''
        Called when someone has messaged our chat.
        '''
        await self.send(text_data=json.dumps(
                {
                    "purpose": "chat",
                    "message": event["message"],
                    "username": event["username"]
                }
            ))

    async def log_message(self, event):
        '''
        Called when someone has messaged our chat.
        '''
        await self.send(text_data=json.dumps(
                {
                    "purpose": "log",
                    "message": event["message"],
                }
            ))
    
    async def unexpected_message(self, event):
        pass
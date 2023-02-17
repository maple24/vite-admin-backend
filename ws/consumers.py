import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser


class ChannelConsumer(AsyncWebsocketConsumer):
    '''
    when a client send a message, the message will be received by consumer first and then broadcast to channel layer, and then to other group memebers 
    '''
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"group_{self.room_name}"
        
        if self.room_group_name == "group_chat":
            # chat room, authentication is required
            # 127.0.0.1 will be considered as anonymous, use localhost
            if self.scope['user'].is_anonymous:
                return AnonymousUser()
        elif self.room_group_name == "group_log":
            # log room, no authentication is required
            pass
        self.user = self.scope['user'].username
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
        purpose = text_data_json.get("purpose")
        method = text_data_json.get("method")
        args = text_data_json.get("args", "No args found!")

        handler_func_map = {
            "chat": "chat_message",
            "log": "log_message",
            "terminal": 'terminal_message'
        }
        # Send events over the channel layer (broadcast)
        hanlder_func = handler_func_map.get(purpose, "unexpected_message")
            
        await self.channel_layer.group_send(
            self.room_group_name, 
            {
                "type": hanlder_func,
                # "room_id": room_id,
                "username": self.user,
                "args": args
            }
        )

    # handling function to receive events and transmit them into websockets 
    async def chat_message(self, event):
        '''
        Called when someone has messaged our chat.
        '''
        await self.send(text_data=json.dumps(
                {
                    "args": event["args"],
                    "username": event["username"]
                }
            ))

    async def log_message(self, event):
        '''
        Called when someone has messaged our chat.
        '''
        await self.send(text_data=json.dumps(
                {
                    "args": event["args"],
                }
            ))
    
    async def terminal_message(self, event):
        await self.send(text_data=json.dumps(
                {
                    "args": event["args"],
                }
            ))
    
    async def unexpected_message(self, event):
        pass
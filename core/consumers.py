import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from .models import Message
from core import consumers

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        # Join group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender = data['sender']
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))

        # Save to DB if the user is authenticated
    #     if user.is_authenticated:
    #         await self.save_message(self.lawyer_id, user, message)

    #     await self.channel_layer.group_send(
    #         self.room_group_name,
    #         {
    #             'type': 'chat_message',
    #             'message': f"{user.username if user.is_authenticated else 'Anonymous'}: {message}"
    #         }
    #     )

    # @sync_to_async
    # def save_message(self, lawyer_id, user, message):
    #     Message.objects.create(
    #         lawyer_id=lawyer_id,
    #         sender=user,
    #         text=message
    #     )

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.lawyer_id = self.scope['url_route']['kwargs']['lawyer_id']
#         self.room_group_name = f"chat_{self.lawyer_id}"

#         # Join group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     # Receive message from WebSocket
#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data['message']
#         user = self.scope["user"].username if self.scope["user"].is_authenticated else "Anonymous"

#         # Broadcast to group
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': f"{user}: {message}"
#             }
#         )

#     # Receive message from group
#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps({
#             'message': event['message']
#         }))



# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope['url_route']['kwargs']['room_name']
#         self.room_group_name = f'chat_{self.room_name}'

#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data['message']
#         sender = data['sender']

#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message,
#                 'sender': sender,
#             }
#         )

#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps({
#             'message': event['message'],
#             'sender': event['sender'],
#         }))

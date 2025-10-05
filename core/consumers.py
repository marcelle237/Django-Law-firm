import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from .models import Message
from core import consumers
from channels.db import database_sync_to_async


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
        message = data.get('message')
        sender = data.get('sender')
        signal = data.get('signal')

        if message:
            await self.save_message(self.room_name, message, sender)
            # Handle WebRTC signaling messages
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': sender,
                }
            )
        
        if signal:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'signal_message',
                    'signal': signal,
                    'sender': sender,
                }
            )
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))


    async def signal_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'signal',
            'signal': event['signal'],
            'sender': event['sender'],
        }))


    @database_sync_to_async
    def save_message(self, room_name, sender_username, text):
        try:
            sender = User.objects.get(username=sender_username)
        except User.DoesNotExist:
            return
        Message.objects.create(room_name=room_name, sender=sender, text=text)

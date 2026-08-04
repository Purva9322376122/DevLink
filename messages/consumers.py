import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()


class MessagesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f"messages_{self.conversation_id}"

        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        # Verify that the user is a participant
        is_participant = await database_sync_to_async(self._is_participant)()
        if not is_participant:
            await self.close(code=4004)
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    def _is_participant(self):
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
        except Conversation.DoesNotExist:
            return False
        return conv.participants.filter(id=self.scope['user'].id).exists()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        msg_type = data.get('type', 'chat.message')

        if msg_type == 'chat.message':
            content = data.get('message', '').strip()
            if not content:
                return
            # Save message
            msg = await database_sync_to_async(self._save_message)(content)

            payload = {
                'type': 'chat.message',
                'message': msg.content,
                'sender': msg.sender.username,
                'sender_id': msg.sender.id,
                'message_id': msg.id,
                'timestamp': msg.timestamp.isoformat(),
            }

            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat_message',
                'payload': payload,
            })

    def _save_message(self, content):
        conv = Conversation.objects.get(id=self.conversation_id)
        msg = Message.objects.create(conversation=conv, sender=self.scope['user'], content=content)
        return msg

    # Handlers for messages sent to the group
    async def chat_message(self, event):
        payload = event['payload']
        await self.send(text_data=json.dumps(payload))

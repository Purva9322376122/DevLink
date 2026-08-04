"""
Chat WebSocket consumer with typing indicators, delivery receipts, read receipts, and presence.
Room name: chat_{min_uid}_{max_uid}
Presence group: presence_user_{user_id}
"""
import json
import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.apps import apps
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.other_username = self.scope['url_route']['kwargs']['username']
        self.other_user_id = await self._get_user_id(self.other_username)
        
        if not self.other_user_id:
            await self.close(code=4004)  # User not found
            return

        # Stable room key regardless of who initiates
        uids = sorted([self.user.id, self.other_user_id])
        self.room_group_name = f"chat_{uids[0]}_{uids[1]}"
        
        # Presence tracking
        self.presence_group = f"presence_user_{self.other_user_id}"
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.presence_group, self.channel_name)
        await self.accept()
        
        # Notify other user that this user is online
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_online',
            'username': self.user.username,
            'user_id': self.user.id,
        })
        
        # Send current presence state to newly connected user
        is_other_online = await self._is_user_online(self.other_user_id)
        await self.send(text_data=json.dumps({
            'type': 'presence.status',
            'username': self.other_username,
            'is_online': is_other_online,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Notify other user that this user is offline
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'user_offline',
                'username': self.user.username,
                'user_id': self.user.id,
            })
            
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            await self.channel_layer.group_discard(self.presence_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'chat.message')

        if msg_type == 'chat.message':
            await self._handle_chat_message(data)
        elif msg_type == 'typing.start':
            await self._handle_typing_start()
        elif msg_type == 'typing.stop':
            await self._handle_typing_stop()
        elif msg_type == 'message.read':
            await self._handle_message_read(data)
        elif msg_type == 'message.delivered':
            await self._handle_message_delivered(data)

    async def _handle_chat_message(self, data):
        """Handle incoming chat message."""
        content = data.get('message', '').strip()
        file_url = data.get('file_url')
        file_type = data.get('file_type')  # 'image' or 'file'
        
        if not content and not file_url:
            return

        other_user = await self._get_user(self.other_username)
        saved = await self._save_message(
            self.user, other_user, content, file_url, file_type
        )

        # Broadcast message to chat room
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'message': saved.content,
            'sender': self.user.username,
            'sender_id': self.user.id,
            'message_id': saved.id,
            'timestamp': saved.timestamp.isoformat(),
            'file_url': saved.file_url,
            'file_type': saved.file_type,
        })

    async def _handle_typing_start(self):
        """Handle typing indicator start."""
        # Broadcast typing indicator to chat room (but not back to sender)
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'typing_indicator',
            'username': self.user.username,
            'is_typing': True,
        })

    async def _handle_typing_stop(self):
        """Handle typing indicator stop."""
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'typing_indicator',
            'username': self.user.username,
            'is_typing': False,
        })

    async def _handle_message_read(self, data):
        """Handle message read receipt."""
        message_id = data.get('message_id')
        if message_id:
            await self._mark_message_read(message_id)
            
            # Broadcast read receipt to chat room
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'message_read',
                'message_id': message_id,
                'read_by': self.user.username,
            })

    async def _handle_message_delivered(self, data):
        """Handle message delivered receipt."""
        message_id = data.get('message_id')
        if message_id:
            await self._mark_message_delivered(message_id)

    # ── WebSocket event handlers (from group_send) ────────────────────────────

    async def chat_message(self, event):
        """Relay chat message to connected clients."""
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'message_id': event.get('message_id'),
            'timestamp': event.get('timestamp'),
            'file_url': event.get('file_url'),
            'file_type': event.get('file_type'),
        }))
        
        # Auto-mark as delivered when received
        if event.get('message_id') and event['sender_id'] != self.user.id:
            await self._mark_message_delivered(event['message_id'])

    async def typing_indicator(self, event):
        """Relay typing indicator to connected clients."""
        # Don't send back to the person who sent the typing indicator
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'chat.typing',
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    async def message_read(self, event):
        """Relay message read receipt to connected clients."""
        await self.send(text_data=json.dumps({
            'type': 'message.read',
            'message_id': event['message_id'],
            'read_by': event['read_by'],
        }))

    async def user_online(self, event):
        """Notify that a user is online."""
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'presence.online',
                'username': event['username'],
                'user_id': event['user_id'],
            }))

    async def user_offline(self, event):
        """Notify that a user is offline."""
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'presence.offline',
                'username': event['username'],
                'user_id': event['user_id'],
            }))

    # ── Database helpers ──────────────────────────────────────────────────────

    @database_sync_to_async
    def _get_user_id(self, username: str) -> int:
        User = apps.get_model('auth', 'User')
        try:
            return User.objects.values_list('id', flat=True).get(username=username)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_user(self, username: str):
        User = apps.get_model('auth', 'User')
        return User.objects.get(username=username)

    @database_sync_to_async
    def _save_message(self, sender, receiver, content, file_url=None, file_type=None):
        Message = apps.get_model('opportunities', 'Message')
        return Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=content,
            file_url=file_url,
            file_type=file_type,
            is_delivered=False,  # Mark as delivered only when received
        )

    @database_sync_to_async
    def _mark_message_delivered(self, message_id: int) -> None:
        Message = apps.get_model('opportunities', 'Message')
        msg = Message.objects.filter(id=message_id).first()
        if msg and not msg.is_delivered:
            msg.mark_delivered()

    @database_sync_to_async
    def _mark_message_read(self, message_id: int) -> None:
        Message = apps.get_model('opportunities', 'Message')
        msg = Message.objects.filter(id=message_id).first()
        if msg and not msg.is_read:
            msg.mark_read()

    @database_sync_to_async
    def _is_user_online(self, user_id: int) -> bool:
        """Check if a user has any active WebSocket connections."""
        from channels.layers import get_channel_layer
        # This is a simplified check - in production, use Redis to track presence
        return False  # TODO: Implement proper presence tracking with Redis

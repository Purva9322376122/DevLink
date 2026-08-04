"""
NotificationConsumer — personal WebSocket channel per authenticated user.
Group name: notifications_{user_id}

Clients connect at: ws://<host>/ws/notifications/
"""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send current unread count on connect so the badge is up-to-date
        count = await self._get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'notification.count_update',
            'unread_count': count,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle mark-as-read messages from the client."""
        data = json.loads(text_data)
        if data.get('type') == 'mark_read':
            notification_id = data.get('id')
            if notification_id:
                await self._mark_read(notification_id)
                count = await self._get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'notification.count_update',
                    'unread_count': count,
                }))

    # ── Channel layer event handlers (called by group_send) ──────────────────

    async def notification_new(self, event):
        """Relay a new notification to the connected client."""
        await self.send(text_data=json.dumps({
            'type': 'notification.new',
            **{k: v for k, v in event.items() if k != 'type'},
        }))
        # Update badge count
        count = await self._get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'notification.count_update',
            'unread_count': count,
        }))

    async def notification_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification.count_update',
            'unread_count': event['unread_count'],
        }))

    # ── DB helpers ────────────────────────────────────────────────────────────

    @database_sync_to_async
    def _get_unread_count(self) -> int:
        from notifications.models import Notification
        return Notification.objects.filter(
            recipient=self.user, is_read=False
        ).count()

    @database_sync_to_async
    def _mark_read(self, notification_id: int) -> None:
        from notifications.models import Notification
        Notification.objects.filter(
            id=notification_id, recipient=self.user
        ).update(is_read=True)

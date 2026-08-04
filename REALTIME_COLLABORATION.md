# Real-Time Collaboration System Documentation

## Overview

The real-time collaboration system enables live, multi-user interactions across chat, project management, issue tracking, and Kanban boards using Django Channels and WebSocket technology. The architecture is designed for Redis scalability while maintaining compatibility with development environments.

## Architecture

### Core Components

1. **Django Channels** - WebSocket server and async task handling
2. **Redis Channel Layer** - Message broker for multi-server deployments
3. **Presence Manager** - User state tracking with cache backend
4. **WebSocket Consumers** - Async event handlers for real-time updates
5. **Broadcast Services** - Centralized message distribution
6. **Signal Handlers** - Django signals triggering real-time broadcasts

### Data Flow

```
User Action (Model Save)
    ↓
Django Signal
    ↓
Broadcast Service
    ↓
Channel Layer (Redis)
    ↓
WebSocket Consumer
    ↓
Connected Clients (JSON)
```

## WebSocket Connections

### Available Endpoints

| Endpoint | Purpose | Room Format |
|----------|---------|-------------|
| `ws://host/ws/chat/{username}/` | 1-on-1 messaging | `chat_{min_uid}_{max_uid}` |
| `ws://host/ws/projects/{project_id}/` | Project updates & presence | `project_{project_id}` |
| `ws://host/ws/issues/{issue_id}/` | Issue comments & typing | `issue_{issue_id}` |
| `ws://host/ws/kanban/{project_id}/` | Kanban board sync | `kanban_{project_id}` |
| `ws://host/ws/notifications/` | User notifications | `notifications_{user_id}` |

## Event Protocol

### Chat Events

#### Send Message
```json
{
    "type": "chat.message",
    "data": {
        "content": "Hello! How are you?",
        "recipient_id": 42
    }
}
```

Response (broadcast to both users):
```json
{
    "type": "chat.message",
    "data": {
        "id": 123,
        "sender_id": 10,
        "recipient_id": 42,
        "content": "Hello! How are you?",
        "timestamp": "2024-01-15T10:30:45Z",
        "is_delivered": true,
        "is_read": false
    }
}
```

#### Typing Indicator
```json
{
    "type": "typing.start",
    "data": {"recipient_id": 42}
}
```

Broadcast (to the other user):
```json
{
    "type": "typing.indicator",
    "data": {
        "user_id": 10,
        "username": "alice",
        "is_typing": true
    }
}
```

#### Message Read Receipt
```json
{
    "type": "message.read",
    "data": {"message_id": 123}
}
```

Broadcast (to sender):
```json
{
    "type": "message_read",
    "data": {
        "message_id": 123,
        "reader_id": 42,
        "timestamp": "2024-01-15T10:31:00Z"
    }
}
```

### Issue Events

#### Issue Created (Broadcast)
```json
{
    "type": "issue.created",
    "data": {
        "id": 5,
        "number": 42,
        "title": "Fix login bug",
        "status": "open",
        "priority": "high",
        "created_by": "alice",
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

#### Issue Status Changed (Broadcast)
```json
{
    "type": "issue.status_changed",
    "data": {
        "id": 5,
        "number": 42,
        "old_status": "open",
        "new_status": "closed",
        "changed_by": "bob"
    }
}
```

#### Issue Comment Added (Broadcast)
```json
{
    "type": "comment.added",
    "data": {
        "id": 123,
        "issue_id": 5,
        "issue_number": 42,
        "author": "alice",
        "body": "I've identified the root cause",
        "created_at": "2024-01-15T10:32:00Z"
    }
}
```

### Kanban Events

#### Card Moved (Broadcast)
```json
{
    "type": "card.moved",
    "data": {
        "card_id": 15,
        "old_column": "To Do",
        "new_column": "In Progress",
        "old_position": 2,
        "new_position": 0,
        "moved_by": "alice"
    }
}
```

#### Card Updated (Broadcast)
```json
{
    "type": "card.updated",
    "data": {
        "card_id": 15,
        "title": "Updated title",
        "description": "Updated description",
        "column": "In Progress"
    }
}
```

### Presence Events

#### User Joined (Broadcast)
```json
{
    "type": "presence.user_joined",
    "data": {
        "user_id": 10,
        "username": "alice",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

#### User Left (Broadcast)
```json
{
    "type": "presence.user_left",
    "data": {
        "user_id": 10,
        "username": "alice",
        "timestamp": "2024-01-15T10:35:00Z"
    }
}
```

### Notification Events

#### New Notification (Broadcast)
```json
{
    "type": "notification.new",
    "data": {
        "id": 789,
        "verb": "issue_assigned",
        "actor": "alice",
        "description": "You were assigned to issue #42",
        "timestamp": "2024-01-15T10:30:00Z",
        "is_read": false
    }
}
```

## Client Implementation

### JavaScript Example

```javascript
// Connect to chat
const username = 'alice';
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + username + '/'
);

// Handle connection
chatSocket.onopen = function(e) {
    console.log('Chat connected');
};

// Send message
function sendMessage(recipientId, content) {
    chatSocket.send(JSON.stringify({
        'type': 'chat.message',
        'data': {
            'content': content,
            'recipient_id': recipientId,
        }
    }));
}

// Start typing
function startTyping(recipientId) {
    chatSocket.send(JSON.stringify({
        'type': 'typing.start',
        'data': {'recipient_id': recipientId}
    }));
}

// Handle incoming events
chatSocket.onmessage = function(e) {
    const event = JSON.parse(e.data);
    
    switch(event.type) {
        case 'chat.message':
            onMessageReceived(event.data);
            break;
        case 'typing.indicator':
            onTypingIndicator(event.data);
            break;
        case 'message_read':
            onMessageRead(event.data);
            break;
    }
};

// Handle disconnection
chatSocket.onclose = function(e) {
    console.log('Chat disconnected');
};
```

### Python Example (Testing)

```python
import asyncio
import json
from channels.testing import WebsocketCommunicator
from projects.consumers import ChatConsumer

async def test_chat():
    communicator = WebsocketCommunicator(
        ChatConsumer.as_asgi(),
        '/ws/chat/alice/',
        headers=[(b'origin', b'testserver')]
    )
    
    # Connect
    connected, subprotocol = await communicator.connect()
    assert connected
    
    # Send message
    await communicator.send_json_to({
        'type': 'chat.message',
        'data': {
            'content': 'Hello!',
            'recipient_id': 42
        }
    })
    
    # Receive response
    response = await communicator.receive_json_from()
    assert response['type'] == 'chat.message'
    assert response['data']['content'] == 'Hello!'
    
    # Disconnect
    await communicator.disconnect()
```

## Configuration

### Development Environment

```python
# settings.py
INSTALLED_APPS = [
    ...
    'channels',
    'daphne',
]

ASGI_APPLICATION = 'devlink.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# Cache settings (for presence tracking)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

### Production Environment (Redis)

```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis', 6379)],
            'group_expiry': 86400,
        },
    },
}

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}
```

### ASGI Configuration

```python
# devlink/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

from projects.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devlink.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

## Presence Tracking

### API Usage

```python
from projects.presence import PresenceManager

manager = PresenceManager()

# User comes online
manager.user_online_in_project(
    user_id=10,
    project_id=1,
    username='alice'
)

# Get online users in project
online_users = manager.get_online_users_in_project(project_id=1)
# Returns: [{'user_id': 10, 'username': 'alice', 'timestamp': '2024-01-15T10:30:00Z'}, ...]

# User goes offline
manager.user_offline_in_project(user_id=10, project_id=1)

# Clear all presence for user on logout
manager.clear_user_presence(user_id=10)
```

## Broadcasting

### Programmatic Broadcasting

```python
from projects.services import broadcast_to_project, broadcast_to_issue, broadcast_to_kanban

# Broadcast to project
broadcast_to_project(
    project_id=1,
    event_type='issue_updated',
    data={
        'id': 5,
        'title': 'Updated title',
        'status': 'closed'
    }
)

# Broadcast to issue
broadcast_to_issue(
    issue_id=5,
    event_type='comment_added',
    data={
        'id': 123,
        'author': 'alice',
        'body': 'Comment text'
    }
)

# Broadcast to Kanban board
broadcast_to_kanban(
    project_id=1,
    event_type='card_moved',
    data={
        'card_id': 15,
        'new_column': 'Done'
    }
)
```

### Automatic Broadcasting via Signals

Django signals automatically trigger broadcasts when models change:

- **Issue Created** → `issue.created` broadcast
- **Issue Updated** → `issue.updated` broadcast
- **Issue Status Changed** → `issue.status_changed` broadcast
- **Issue Assigned** → `issue.assigned` broadcast
- **Issue Deleted** → `issue.deleted` broadcast
- **Comment Added** → `comment.added` broadcast
- **Kanban Card Created** → `card.created` broadcast
- **Kanban Card Updated** → `card.updated` broadcast
- **Kanban Card Deleted** → `card.deleted` broadcast

## Error Handling

### Graceful Degradation

The system gracefully handles Redis/channel layer failures:

```python
from projects.realtime_config import ChannelConfig

channel_layer = ChannelConfig.get_channel_layer()
if not channel_layer:
    # Channel layer unavailable, system continues in limited mode
    # Messages still saved to database
    # Real-time updates won't work until Redis is back
    pass
```

### Event Validation

```python
from projects.realtime_errors import EventValidator

is_valid, error = EventValidator.validate_event(
    'chat.message',
    {'content': 'Hello!', 'recipient_id': 42}
)

if not is_valid:
    print(f"Invalid event: {error}")
```

## Monitoring

### Logging

All real-time events are logged to `devlink.realtime` logger:

```python
import logging

logger = logging.getLogger('devlink.realtime')
# Logs include event types, user IDs, timestamps, and errors
```

### Health Checks

```python
from projects.realtime_errors import ConnectionHealthCheck

# Check channel layer
is_healthy = await ConnectionHealthCheck.check_channel_layer()

# Check WebSocket connection
is_connected = await ConnectionHealthCheck.check_websocket_connection(consumer)
```

## Performance Considerations

1. **Channel Groups** - Each group can handle thousands of subscribers efficiently
2. **Message Ordering** - Messages are ordered by database timestamp
3. **Presence TTL** - 5-minute default TTL for presence tracking
4. **Redis Memory** - Groups expire after 24 hours (configurable)
5. **Connection Pooling** - Redis client handles connection reuse

## Testing

### Running Tests

```bash
# Run all real-time tests
python manage.py test projects.tests_realtime

# Run integration tests
python manage.py test projects.tests_integration

# Run specific test class
python manage.py test projects.tests_realtime.TestPresenceTracking

# Run with coverage
coverage run --source='.' manage.py test projects.tests_realtime
coverage report
```

## Troubleshooting

### Issue: WebSocket connection fails
- **Check**: Is `daphne` running? (`python manage.py runserver` won't work, use `daphne -b 0.0.0.0 -p 8000 devlink.asgi:application`)
- **Check**: Is authentication middleware configured?
- **Check**: Are URL patterns correct in `routing.py`?

### Issue: Messages not appearing in real-time
- **Check**: Is Redis running? (`redis-cli ping` should return `PONG`)
- **Check**: Are signal handlers registered in `apps.py`?
- **Check**: Are channel groups being joined on connect?

### Issue: Presence not tracking correctly
- **Check**: Is cache backend configured?
- **Check**: Is presence TTL appropriate for your use case?
- **Check**: Are `user_online_in_project` calls made on connect?

### Issue: High Redis memory usage
- **Solution**: Reduce `group_expiry` in channel layer config
- **Solution**: Reduce presence TTL
- **Solution**: Implement periodic cleanup of inactive users

## Security

1. **Authentication** - `AuthMiddlewareStack` validates user on connect
2. **Authorization** - Consumers verify user has project/issue access
3. **Rate Limiting** - Consider adding rate limits to prevent abuse
4. **Message Validation** - All incoming events are validated
5. **SQL Injection** - ORM usage prevents SQL injection

## Future Enhancements

1. Message reactions/emojis
2. Message editing with history
3. Chat room archives
4. Activity feeds
5. Collaborative editing indicators
6. Message search integration
7. Rich media support (with restricted file types)
8. End-to-end encryption option
9. Slack-like threads
10. Real-time notification aggregation

## API Reference

See `projects/websocket_protocol.py` for complete event protocol specification.

See `projects/consumers.py` for consumer implementation details.

See `projects/services.py` for broadcast service API.

See `projects/presence.py` for presence management API.

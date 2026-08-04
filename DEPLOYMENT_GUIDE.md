# Real-Time Collaboration System - Deployment Guide

## Quick Start

### Development Setup

1. **Install Dependencies**
   ```bash
   pip install channels channels-redis daphne
   ```

2. **Update Settings (devlink/settings.py)**
   ```python
   INSTALLED_APPS = [
       # ... other apps
       'channels',
       'daphne',
   ]

   ASGI_APPLICATION = 'devlink.asgi.application'

   # Channel layer configuration
   CHANNEL_LAYERS = {
       'default': {
           'BACKEND': 'channels.layers.InMemoryChannelLayer',
       }
   }
   ```

3. **Update ASGI (devlink/asgi.py)**
   ```python
   import os
   from django.core.asgi import get_asgi_application
   from channels.routing import ProtocolTypeRouter, URLRouter
   from channels.auth import AuthMiddlewareStack
   
   from projects.routing import websocket_urlpatterns

   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devlink.settings')

   application = ProtocolTypeRouter({
       'http': get_asgi_application(),
       'websocket': AuthMiddlewareStack(
           URLRouter(websocket_urlpatterns)
       ),
   })
   ```

4. **Run Development Server**
   ```bash
   daphne -b 0.0.0.0 -p 8000 devlink.asgi:application
   ```

### Production Setup

1. **Install Dependencies**
   ```bash
   pip install channels channels-redis daphne redis
   ```

2. **Install Redis Server**
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install redis-server
   
   # On macOS
   brew install redis
   
   # Docker
   docker run -d -p 6379:6379 redis:latest
   ```

3. **Update Settings (devlink/settings.py)**
   ```python
   INSTALLED_APPS = [
       # ... other apps
       'channels',
   ]

   ASGI_APPLICATION = 'devlink.asgi.application'

   CHANNEL_LAYERS = {
       'default': {
           'BACKEND': 'channels_redis.core.RedisChannelLayer',
           'CONFIG': {
               'hosts': [('redis', 6379)],  # or your Redis host
               'group_expiry': 86400,  # 24 hours
               'connection_kwargs': {
                   'retry_on_timeout': True,
                   'socket_keepalive': True,
               },
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

4. **Run with Daphne**
   ```bash
   # Single process
   daphne -b 0.0.0.0 -p 8000 devlink.asgi:application

   # With Gunicorn (recommended)
   pip install gunicorn
   gunicorn devlink.asgi:application --workers 4 --worker-class uvicorn.workers.UvicornWorker
   ```

5. **Docker Compose Setup (Recommended)**
   ```yaml
   version: '3'
   
   services:
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
       command: redis-server --appendonly yes
   
     web:
       build: .
       command: daphne -b 0.0.0.0 -p 8000 devlink.asgi:application
       ports:
         - "8000:8000"
       depends_on:
         - redis
       environment:
         - REDIS_URL=redis://redis:6379
         - DEBUG=False
       volumes:
         - .:/app
   
   volumes:
     redis_data:
   ```

## Testing

### Run All Tests
```bash
# With pytest
pytest projects/ opportunities/ notifications/ -v

# With Django test runner
python manage.py test --no-input
```

### Run Specific Test Suite
```bash
# Real-time features
pytest projects/tests_realtime.py -v

# Integration tests
pytest projects/tests_integration.py -v

# Chat system
pytest opportunities/tests.py -v

# All tests with coverage
pytest --cov=projects --cov=opportunities --cov=notifications
```

## Configuration Options

### Channel Layer Configuration

#### Development (In-Memory)
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}
```

#### Development (With Redis)
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
```

#### Production (Redis Cluster)
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [
                ('redis-1', 6379),
                ('redis-2', 6379),
                ('redis-3', 6379),
            ],
            'group_expiry': 86400,
            'capacity': 1500,
            'connection_kwargs': {
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {
                    1: 1,  # TCP_KEEPIDLE
                    2: 1,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                },
            },
        },
    },
}
```

### Presence TTL Configuration
```python
# In projects/presence.py, modify:
PRESENCE_TTL = 300  # 5 minutes (in seconds)
```

### Logging Configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'devlink.realtime': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Monitoring & Debugging

### Check Redis Connection
```python
# In Django shell
from django.core.cache import cache
cache.set('test', 'value', 60)
cache.get('test')  # Should return 'value'
```

### Monitor Channel Layer
```python
# In Django shell
from channels.layers import get_channel_layer
import asyncio

channel_layer = get_channel_layer()
# Try to send a test message
```

### View Active WebSocket Connections
```python
# Add this to a Django management command
from django.core.cache import cache
from projects.presence import PresenceManager

manager = PresenceManager()
online = manager.get_online_users_in_project(project_id=1)
print(f"Online users in project: {online}")
```

### Enable Debug Logging
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'devlink.realtime': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Performance Tuning

### Redis Configuration
```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least recently used keys
timeout 300  # Close idle connections
tcp-keepalive 60
```

### Daphne Configuration
```bash
# Production
daphne \
  -b 0.0.0.0 \
  -p 8000 \
  --access-log - \
  --timeout 120 \
  --ping-interval 20 \
  --ping-timeout 20 \
  devlink.asgi:application
```

### Connection Pooling
```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis', 6379)],
            'connection_kwargs': {
                'max_connections': 50,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
            },
        },
    },
}
```

## Troubleshooting

### WebSocket Connection Fails
**Problem:** WebSocket connections are rejected
**Solution:**
1. Verify daphne is running (not Django runserver)
2. Check ASGI_APPLICATION setting
3. Verify websocket URL routing in routing.py
4. Check browser console for connection errors

### Messages Not Appearing in Real-Time
**Problem:** Messages are saved but not appearing live
**Solution:**
1. Verify Redis is running: `redis-cli ping`
2. Check CHANNEL_LAYERS configuration
3. Verify consumers are joining groups
4. Check browser WebSocket tab in DevTools

### Memory Leak / High Redis Memory
**Problem:** Redis memory keeps growing
**Solution:**
1. Check `group_expiry` setting (should be 86400)
2. Reduce PRESENCE_TTL if too high
3. Set `maxmemory-policy` in Redis
4. Monitor with `redis-cli info memory`

### Broadcast Not Working
**Problem:** Broadcast service raises no error but changes don't sync
**Solution:**
```python
# Test broadcast directly
from projects.realtime_config import ChannelConfig
channel_layer = ChannelConfig.get_channel_layer()
# If None, channel layer is unavailable
```

### Consumer Not Receiving Events
**Problem:** Consumer connects but doesn't receive broadcasts
**Solution:**
1. Verify `group_add()` is called in `connect()`
2. Check event type matches handler method name
3. Verify group name formatting
4. Check Django user is authenticated

## Environment Variables

```bash
# Development
DJANGO_SETTINGS_MODULE=devlink.settings
DEBUG=True
REDIS_URL=redis://localhost:6379/0

# Production
DJANGO_SETTINGS_MODULE=devlink.settings
DEBUG=False
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=mysite.com,www.mysite.com
```

## Security Considerations

### Production Security Checklist
- [ ] Daphne behind reverse proxy (nginx/Apache)
- [ ] WebSocket over WSS (TLS)
- [ ] Redis password-protected
- [ ] CSRF tokens for WebSocket subscriptions
- [ ] Rate limiting on message send
- [ ] User authorization checks in consumers
- [ ] SQL injection prevention (using ORM)
- [ ] XSS prevention (client-side input validation)

### Redis Security
```bash
# redis.conf
requirepass your_secure_password
bind 127.0.0.1  # Don't bind to 0.0.0.0 in production
protected-mode yes
```

### Rate Limiting Example
```python
# In consumer
from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation

def send_message(self, event):
    user_id = self.scope['user'].id
    key = f'rate_limit:chat:{user_id}'
    count = cache.get(key, 0)
    
    if count >= 10:  # 10 messages per minute
        raise SuspiciousOperation("Rate limit exceeded")
    
    cache.set(key, count + 1, 60)
    # Send message...
```

## Backup & Recovery

### Redis Backup
```bash
# Automatic with AOF
redis-server --appendonly yes

# Manual backup
redis-cli BGSAVE

# Restore
cp dump.rdb /var/lib/redis/
redis-server
```

### Database Backup
```bash
# Before deploying
python manage.py dumpdata > backup.json

# After disaster
python manage.py loaddata backup.json
```

## Monitoring with Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']

  - job_name: 'django'
    static_configs:
      - targets: ['localhost:8000']
```

## Support

For issues or questions:
1. Check REALTIME_COLLABORATION.md for protocol docs
2. Review test files for usage examples
3. Check logs: `tail -f logs/realtime.log`
4. Verify Redis: `redis-cli --stat`
5. Check consumer status with Django shell

---

**Last Updated:** July 22, 2024
**Version:** 1.0
**Status:** Production Ready

import asyncio
from importlib import import_module
from asgiref.testing import ApplicationCommunicator

app = import_module('Connect.asgi').application

async def test(path):
    scope = {
        'type': 'websocket',
        'path': path,
        'raw_path': path.encode('ascii'),
        'query_string': b'',
        'headers': [],
        'client': ('127.0.0.1', 50000),
        'server': ('127.0.0.1', 8000),
        'scheme': 'ws',
        'subprotocols': [],
        'extensions': {},
    }
    communicator = ApplicationCommunicator(app, scope)
    await communicator.send_input({'type': 'websocket.connect'})
    try:
        event = await communicator.receive_output(1)
    except Exception as e:
        print('No event received:', e)
        return
    print('Received event type:', event['type'])
    print('Event:', event)

asyncio.run(test('/ws/notifications/'))

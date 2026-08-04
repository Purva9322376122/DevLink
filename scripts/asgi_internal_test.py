import asyncio
from importlib import import_module
from asgiref.testing import ApplicationCommunicator

app = import_module('Connect.asgi').application

async def test():
    scope = {'type':'websocket','path':'/ws/notifications/','raw_path':b'/ws/notifications/','query_string':b'','headers':[],'client':('127.0.0.1',50000),'server':('127.0.0.1',8000),'scheme':'ws','subprotocols':[],'extensions':{}}
    communicator = ApplicationCommunicator(app, scope)
    await communicator.send_input({'type':'websocket.connect'})
    try:
        event = await communicator.receive_output(1)
        print('event:',event)
    except Exception as e:
        print('no event or timeout',e)

asyncio.run(test())

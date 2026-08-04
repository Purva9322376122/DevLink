from django.core.management import get_commands
cmd = get_commands().get('runserver')
print('runserver command module:', cmd)
# Print all apps that provide management commands for inspection
commands = get_commands()
from pprint import pprint
pprint({k: v for k, v in list(commands.items())[:50]})

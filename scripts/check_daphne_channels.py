import importlib
m='daphne.management.commands.runserver'
try:
    mod=importlib.import_module(m)
    print('daphne runserver found:', mod)
except Exception as e:
    print('daphne runserver import error:', e)

try:
    import channels
    print('channels version', channels.__version__)
except Exception as e:
    print('channels import error', e)

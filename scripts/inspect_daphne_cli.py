import importlib
m = importlib.import_module('daphne.cli')
print(dir(m))
print('has main?', hasattr(m,'main'))
print('has CommandLineInterface?', hasattr(m,'CommandLineInterface'))

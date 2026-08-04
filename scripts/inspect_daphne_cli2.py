from daphne.cli import CommandLineInterface
import inspect
print([m for m in dir(CommandLineInterface) if not m.startswith('_')])
print(inspect.getsource(CommandLineInterface))

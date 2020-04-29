from argparse import ArgumentParser
from importlib import import_module


def main():
    commands = [
        'run',
        # more
    ]

    parser = ArgumentParser('dataplattform')
    subparsers = parser.add_subparsers(dest='command')

    command_modules = {cmd: import_module(f'dataplattform.cli.commands.{cmd}') for cmd in commands}

    for name, cmd in command_modules.items():
        cmd.init(subparsers.add_parser(name))

    args = parser.parse_args()
    command_modules[args.command].run(args)

from argparse import ArgumentParser
from importlib import import_module
from boto3 import setup_default_session


def main():
    commands = [
        'run',
        'add-ssm',
        'create-cognito-user',
        'generate-encrypted-password',
        'setup-datasource',
        'register-table',
        'database',
        'deploy',
        'configure',
        'prepare-sandbox',
        'move-user-pool-group',
        'test'
    ]

    parser = ArgumentParser('dataplattform')
    parser.add_argument('--profile', dest='profile', required=False,
                        default=None, help='aws profile name')
    subparsers = parser.add_subparsers(dest='command')

    command_modules = {
        cmd: import_module(f'dataplattform.cli.commands.{cmd.replace("-", "_")}')
        for cmd in commands
    }

    for name, cmd in command_modules.items():
        cmd.init(subparsers.add_parser(name))

    args = parser.parse_args()
    if args.profile:
        setup_default_session(profile_name=args.profile)

    if args.command:
        command_modules[args.command].run(args, parser)
    else:
        parser.print_help()

from argparse import ArgumentParser, Namespace
from dataplattform.cli.helper import load_serverless_config, find_file, serverless_environment
from os import environ
from importlib.util import spec_from_file_location, module_from_spec
from json import loads


def init(parser: ArgumentParser):
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    parser.add_argument('-e', '--event', dest='event', default='{}')


def run(args: Namespace):
    config = load_serverless_config('functions')
    handler = next(iter(config.values()))['handler']
    handler_file, handler_func = handler.split('.')

    env = serverless_environment(serverless_config=config)
    for k, v in env.items():
        if args.verbose:
            print(f'ENVIRONMENT {k}: {v}')
        environ[k] = v

    spec = spec_from_file_location(handler_file, find_file(f'{handler_file}.py'))
    handler_module = module_from_spec(spec)
    spec.loader.exec_module(handler_module)

    getattr(handler_module, handler_func)(loads(args.event), None)

from argparse import ArgumentParser, Namespace
from dataplattform.cli.helper import (
    load_serverless_config,
    find_file,
    serverless_environment,
    assume_serverless_role)
from os import environ
from importlib.util import spec_from_file_location, module_from_spec
from json import loads
from time import time
import tracemalloc


def init(parser: ArgumentParser):
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    parser.add_argument('-p', '--profile', dest='profile', action='store_true')
    parser.add_argument('-e', '--event', dest='event', default='{}')


def run(args: Namespace, _):
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

    with assume_serverless_role():

        if args.profile:
            tracemalloc.start()
            start_time = time()

            getattr(handler_module, handler_func)(loads(args.event), None)

            complete_time = time() - start_time
            _, peak_memory_usage = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            print('PROFILE DATA')
            print(f'Execution time: {round(complete_time, 2)} seconds')
            print(f'Memory usage: \t{round(peak_memory_usage/(1024**2), 2)} megabytes')
        else:
            getattr(handler_module, handler_func)(loads(args.event), None)

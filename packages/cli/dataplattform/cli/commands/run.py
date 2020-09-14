from argparse import ArgumentParser, Namespace
from dataplattform.cli.helper import (
    load_serverless_config,
    find_file,
    resovle_cloudformation_imports
)
from os import environ
from dataplattform.testing.events import APIGateway
from importlib.util import spec_from_file_location, module_from_spec
from json import loads
from time import time
import tracemalloc
from typing import Dict
from moto import mock_sqs
from boto3 import resource


def init(parser: ArgumentParser):
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    parser.add_argument('-p', '--profile', dest='profile', action='store_true')
    parser.add_argument('-e', '--event', dest='event', default=None)
    parser.add_argument('--event-type', dest='eventType', default='Schedule', choices=['APIGateway', "Schedule"])
    parser.add_argument('--event-file', dest='eventFile')


def run(args: Namespace, _):
    if (args.eventFile):
        with open(args.eventFile) as json_file:
            args.event = json_file.read()
    elif (args.eventType):
        if args.eventType == 'APIGateway':
            api_gw = APIGateway(headers="{}", body="{}").to_json()
            args.event = api_gw
        else:
            args.event = None

    config = load_serverless_config('functions')
    handlers = [(c['handler'], c['environment']) for c in config.values()]
    runners = [prepare_runner(handler, env, args) for handler, env in handlers]

    if len(runners) == 1:
        runner, setup_env = runners[0]
        setup_env()
        runner(loads(args.event))
    else:
        ingest, process = runners
        ingest_run, ingest_env = ingest
        process_run, process_env = process

        ingest_env()

        with mock_sqs():
            sqs = resource('sqs')
            sqs.create_queue(QueueName=environ.get('SQS_QUEUE_NAME'))
            ingest_run(loads(args.event))
            messages = sqs.get_queue_by_name(QueueName=environ.get('SQS_QUEUE_NAME')).receive_messages()

        process_env()
        process_run({
            'Records': [
                {
                    'messageId': msg.message_id,
                    'body': msg.body,
                    'attributes': msg.attributes,
                    'messageAttributes': msg.message_attributes
                } for msg in messages
            ]
        })


def prepare_runner(handler: str, environment: Dict[str, str], args: Namespace):
    handler_file, handler_func = handler.split('.')

    def setup_env():
        env = resovle_cloudformation_imports(environment)
        for k, v in env.items():
            if args.verbose:
                print(f'ENVIRONMENT {k}: {v}')
            environ[k] = v

    def runner(event):
        if args.verbose:
            print(f'START: {handler}')

        spec = spec_from_file_location(handler_file, find_file(f'{handler_file}.py'))
        handler_module = module_from_spec(spec)
        spec.loader.exec_module(handler_module)

        if args.profile:
            tracemalloc.start()
            start_time = time()

            getattr(handler_module, handler_func)(event, None)

            complete_time = time() - start_time
            _, peak_memory_usage = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            print('PROFILE DATA')
            print(f'Execution time: {round(complete_time, 2)} seconds')
            print(f'Memory usage: \t{round(peak_memory_usage/(1024**2), 2)} megabytes')
        else:
            getattr(handler_module, handler_func)(event, None)

        if args.verbose:
            print(f'COMPLETE: {handler}')

    return runner, setup_env

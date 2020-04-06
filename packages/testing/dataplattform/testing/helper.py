from pathlib import Path
import os
from subprocess import run
from json import loads
import boto3


def serverless_environment(serverless_cli=None, serverless_file=None):
    def find_serverless_file():
        if Path(os.path.join(os.path.dirname(__file__), 'serverless.yml')).exists():
            return os.path.join(os.path.dirname(__file__), 'serverless.yml')
        elif Path(os.path.join(os.getcwd(), 'serverless.yml')).exists():
            return os.path.join(os.getcwd(), 'serverless.yml')
        else:
            return 'serverless.yml'

    serverless_cli = serverless_cli or 'serverless'
    serverless_file = serverless_file or os.path.relpath(find_serverless_file(), os.getcwd())

    p = run([
        serverless_cli, 'print', '--path', 'functions', '--format', 'json', '--config', serverless_file],
        check=True, capture_output=True, shell=True, encoding='utf-8')

    exports = boto3.client('cloudformation').list_exports()['Exports']
    exports = {x['Name']: x['Value'] for x in exports}

    def resolve_imports(value):
        if 'Fn::ImportValue' not in value:
            return value
        return exports[value['Fn::ImportValue']]

    return {k: resolve_imports(v) for k, v in next(iter(loads(p.stdout).values()))['environment'].items()}


def load_serverless_environment(serverless_cli=None, serverless_file=None, verbose=True):
    env = serverless_environment(serverless_cli, serverless_file)
    for k, v in env.items():
        if verbose:
            print(f'ENVIRONMENT {k}: {v}')
        os.environ[k] = v

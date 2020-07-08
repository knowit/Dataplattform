from pathlib import Path
import os
from subprocess import run
from json import loads
import boto3


def cloudformation_exports(client=None):
    client = client or boto3.client('cloudformation')
    exports = client.list_exports()['Exports']
    return {x['Name']: x['Value'] for x in exports}


def find_file(filename):
    if Path(os.path.join(os.path.dirname(__file__), filename)).exists():
        return os.path.join(os.path.dirname(__file__), filename)
    elif Path(os.path.join(os.getcwd(), filename)).exists():
        return os.path.join(os.getcwd(), filename)
    else:
        return filename


def load_serverless_config(path, serverless_cli=None, serverless_file=None):
    serverless_cli = serverless_cli or 'serverless'
    serverless_file = os.path.relpath(serverless_file or find_file('serverless.yml'))

    p = run([
        serverless_cli, 'print', '--path', path, '--format', 'json', '--config', serverless_file],
        check=True, capture_output=True, shell=os.name != 'posix', encoding='utf-8')

    return loads(p.stdout)


def serverless_environment(serverless_cli=None, serverless_file=None, serverless_config=None):
    config = serverless_config or load_serverless_config(
        'functions',
        serverless_cli=serverless_cli,
        serverless_file=serverless_file)

    return resovle_cloudformation_imports(next(iter(config.values()))['environment'])


def resovle_cloudformation_imports(environment, exports=None):
    exports = exports or cloudformation_exports()

    def resolve_imports(value):
        if 'Fn::ImportValue' not in value:
            return value
        return exports[value['Fn::ImportValue']]

    return {k: resolve_imports(v) for k, v in environment.items()}


def load_serverless_environment(serverless_cli=None, serverless_file=None, verbose=True):
    env = serverless_environment(serverless_cli, serverless_file)
    for k, v in env.items():
        if verbose:
            print(f'ENVIRONMENT {k}: {v}')
        os.environ[k] = v

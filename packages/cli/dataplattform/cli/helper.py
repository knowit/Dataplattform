from pathlib import Path
import os
import boto3
import yaml


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


def safe_parse_yaml(path: str) -> dict:
    # Yaml-parser that will ignore Serverless tags
    class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
        def ignore_unknown(self, node):
            return None

    SafeLoaderIgnoreUnknown.add_constructor(None, SafeLoaderIgnoreUnknown.ignore_unknown)

    try:
        return yaml.load(open(path), Loader=SafeLoaderIgnoreUnknown)
    except Exception as e:
        print("\nFailed to parse yaml file: " + path + "\n" + str(e))
        raise e


def load_serverless_config(path, serverless_file=None):
    serverless_file = os.path.relpath(
        serverless_file or find_file('serverless.yml'))

    try:
        config = safe_parse_yaml(serverless_file)
        if path in config.keys():
            return config[path]
        else:
            raise Exception("\nAttempted to parse property \"" + path + "\" from " + serverless_file
                            + ", but no such property was found.")
    except Exception as e:
        print("\nException occurred when attempting to load serverless config from " + serverless_file)
        raise e


def serverless_environment(serverless_file=None, serverless_config=None):
    config = serverless_config or load_serverless_config(
        'functions',
        serverless_file=serverless_file)

    return resovle_cloudformation_imports(next(iter(config.values()))['environment'])


def resovle_cloudformation_imports(environment, exports=None):
    exports = exports or cloudformation_exports()

    def resolve_imports(value):
        if 'Fn::ImportValue' not in value:
            return value
        return exports[value['Fn::ImportValue']]

    return {k: resolve_imports(v) for k, v in environment.items()}


def load_serverless_environment(serverless_file=None, verbose=True):
    env = serverless_environment(serverless_file)
    for k, v in env.items():
        if verbose:
            print(f'ENVIRONMENT {k}: {v}')
        os.environ[k] = v

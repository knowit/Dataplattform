from pathlib import Path
import os
from subprocess import run
from json import loads, dumps
import boto3
import botocore
from datetime import datetime
from contextlib import contextmanager


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

    exports = cloudformation_exports()

    def resolve_imports(value):
        if 'Fn::ImportValue' not in value:
            return value
        return exports[value['Fn::ImportValue']]

    return {k: resolve_imports(v) for k, v in next(iter(config.values()))['environment'].items()}


def load_serverless_environment(serverless_cli=None, serverless_file=None, verbose=True):
    env = serverless_environment(serverless_cli, serverless_file)
    for k, v in env.items():
        if verbose:
            print(f'ENVIRONMENT {k}: {v}')
        os.environ[k] = v


@contextmanager
def assume_serverless_role(serverless_cli=None, serverless_file=None):
    config = load_serverless_config('resources.Resources',
                                    serverless_cli=serverless_cli,
                                    serverless_file=serverless_file)
    config = next(iter([c for c in config.values() if c['Type'] == 'AWS::IAM::Role']))

    client = boto3.client('iam')

    try:
        me = client.get_user()['User']
        role_name = f'LOCAL-{me["UserName"]}-{config["Properties"]["RoleName"]}'

        role = client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=dumps({
                'Version': '2012-10-17',
                'Statement': [{
                    'Effect': 'Allow',
                    'Principal': {
                        'AWS': me['Arn']
                    },
                    'Action': 'sts:AssumeRole'
                }]
            }))['Role']
        role_arn = role['Arn']
    except Exception:
        raise f'Failed to find {config["Properties"]["RoleName"]}, maybe its not deployed?'

    base_session = boto3._get_default_session()._session
    fetcher = botocore.credentials.AssumeRoleCredentialFetcher(
        client_creator=base_session.create_client,
        source_credentials=base_session.get_credentials(),
        role_arn=role_arn)
    creds = botocore.credentials.DeferredRefreshableCredentials(
        method='assume-role',
        refresh_using=fetcher.fetch_credentials,
        time_fetcher=lambda: datetime.datetime.now()
    )
    botocore_session = botocore.session.Session()
    botocore_session._credentials = creds

    boto3.setup_default_session(botocore_session=botocore_session)
    print(f'Assume role "{config["Properties"]["RoleName"]}"')
    try:
        yield
    except Exception:
        import traceback
        print(traceback.format_exc())
    finally:
        boto3.setup_default_session(botocore_session=base_session)
        client.delete_role(RoleName=role_name)

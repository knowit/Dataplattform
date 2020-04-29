from argparse import ArgumentParser, Namespace
import boto3
from dataplattform.cli.helper import cloudformation_exports, find_file, load_serverless_config
from botocore.exceptions import ClientError
import json


def create_crawler(crawler_name, tables, stage, access_path, access_level, cloud_exports, client=None):
    client = client or boto3.client('glue')
    role = cloud_exports[f'{stage}-{access_level}-glue-access']
    database = f'{stage}_{access_level.replace("-", "_")}_database'
    targets = [
        {
            'Path': f's3://{cloud_exports[f"{stage}-datalakeName"]}/{access_path}structured/{table}',
            'Exclusions': ['*_metadata']
        }
        for table in tables
    ]

    client.create_crawler(
        Name=crawler_name,
        Role=role,
        DatabaseName=database,
        Targets={'S3Targets': targets},
        Schedule='cron(0 0 * * ? *)',
        SchemaChangePolicy={
            'UpdateBehavior': 'UPDATE_IN_DATABASE',
            'DeleteBehavior': 'DEPRECATE_IN_DATABASE'
        }
    )

    return {
        'status': 'new',
        'name': crawler_name,
        'role': role,
        'database': database,
        'targets': targets
    }


def add_crawler_target(crawler_name, tables, stage, access_path, current_targets, cloud_exports, client=None):
    client = client or boto3.client('glue')
    targets = [*current_targets, *[
        {
            'Path': f's3://{cloud_exports[f"{stage}-datalakeName"]}/{access_path}structured/{table}',
            'Exclusions': ['*_metadata']
        }
        for table in tables
    ]]

    client.update_crawler(
        Name=crawler_name,
        Targets={'S3Targets': targets},
    )

    return {
        'status': 'append',
        'name': crawler_name,
        'targets': targets
    }


def init(parser: ArgumentParser):
    parser.add_argument('tables', nargs='+')
    parser.add_argument('-s', '--stage', dest='stage', default='dev')
    parser.add_argument('-f', '--serverless-file', dest='serverless_file', default='serverless.yml')


def run(args: Namespace, _):
    client = boto3.client('glue')

    def crawler_state(name: str):
        try:
            res = client.get_crawler(Name=name)
            return res['Crawler']['State'] == 'RUNNING', res['Crawler']['Targets']['S3Targets']
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                return False, None
            raise e

    config = load_serverless_config('custom', serverless_file=find_file(args.serverless_file))

    access_level = config['editable']['accessLevel']
    access_path = config['accessPath']
    exports = cloudformation_exports()
    crawler_name = f'{args.stage}_{access_level.replace("-", "_")}_crawler'
    running, current_crawler_targets = crawler_state(crawler_name)

    if current_crawler_targets is None:
        res = create_crawler(
            crawler_name,
            args.tables,
            args.stage,
            access_path,
            access_level,
            exports,
            client=client)
    else:
        if running:
            client.stop_crawler(Name=crawler_name)

        res = add_crawler_target(
            crawler_name,
            args.tables,
            args.stage,
            access_path,
            current_crawler_targets,
            exports,
            client=client)

    print(json.dumps(res, indent=4))

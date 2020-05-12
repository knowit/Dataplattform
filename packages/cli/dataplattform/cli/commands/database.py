from argparse import ArgumentParser, Namespace
from dataplattform.query.engine import Athena
from botocore.exceptions import ClientError
import pandas as pd
import boto3
import json
import time


def init(parser: ArgumentParser):
    parser.add_argument('-e', '--stage', default='dev', choices=['dev', 'test', 'prod'])
    parser.add_argument('-a', '--access-level', required=True, choices=['1', '2', '3'])

    subparsers = parser.add_subparsers(dest='database_command')
    subparsers.add_parser('update-tables')
    subparsers.add_parser('list-tables')

    table_schema_parser = subparsers.add_parser('table-schema')
    table_schema_parser.add_argument('name')

    query_parser = subparsers.add_parser('query')
    query_parser.add_argument('sql')
    query_parser.add_argument('-o', '--output')
    query_parser.add_argument('-f', '--format', default='csv',
                              choices=['csv', 'markdown', 'excel', 'html', 'json'])


def run(args: Namespace, parser: ArgumentParser):
    def update_tables():
        client = boto3.client('glue')
        try:
            client.start_crawler(
                Name=f'{args.stage}_level_{args.access_level}_crawler')
        except ClientError as e:
            if e.response['Error']['Code'] != 'CrawlerRunningException':
                raise e

        print('Table update starting ...')
        while True:
            response = client.get_crawler_metrics(
                CrawlerNameList=[f'{args.stage}_level_{args.access_level}_crawler'])
            metrics = response['CrawlerMetricsList'][0]

            if metrics['StillEstimating']:
                time.sleep(1)
                continue

            print(f'Estimated time left: {metrics["TimeLeftSeconds"]} seconds')
            break

        while True:
            response = client.get_crawler(
                Name=f'{args.stage}_level_{args.access_level}_crawler')
            crawler = response['Crawler']
            if crawler['State'] != 'READY':
                print(f'Status: {crawler["State"]}', end='')
                print('\r', end='')
                time.sleep(1)
                continue

            print(f'Status: {crawler["LastCrawl"]["Status"]}')
            break

        response = client.get_crawler_metrics(
            CrawlerNameList=[f'{args.stage}_level_{args.access_level}_crawler'])
        metrics = response['CrawlerMetricsList'][0]

        print(json.dumps({
            'run_time': metrics['LastRuntimeSeconds'],
            'created': metrics['TablesCreated'],
            'updated': metrics['TablesUpdated']
        }, indent=4))

        print('Tables: ')
        list_tables()

    def list_tables():
        client = boto3.client('glue')
        response = client.get_tables(
            DatabaseName=f'{args.stage}_level_{args.access_level}_database')

        tables = [table['Name'] for table in response['TableList']]
        print(json.dumps(tables, indent=4))

    def table_schema():
        client = boto3.client('glue')
        response = client.get_table(
            DatabaseName=f'{args.stage}_level_{args.access_level}_database',
            Name=args.name)

        columns = [f'\t- {x["Name"]}: {x["Type"]}' for x in response['Table']['StorageDescriptor']['Columns']]
        partition = [f'\t- {x["Name"]}: {x["Type"]}' for x in response['Table']['PartitionKeys']]
        print('\n'.join(['Columns:'] + columns + ['Partitions:'] + partition))

    def query():
        ath = Athena(
            staging_dir=f's3://{args.stage}-datalake-datalake/data/level-{args.access_level}/athena-stage',
            stage=args.stage,
            schema_name=f'{args.stage}_level_{args.access_level}_database')

        df = ath.execute(args.sql).as_pandas()
        if args.output:
            format_options = {
                'csv': {'index': False},
                'markdown': {'showindex': False, 'tablefmt': 'github'},
                'excel': {'index': False},
                'html': {'index': False},
                'json': {'orient': 'records'}
            }
            if args.format in ['markdown']:
                with open(args.output, 'w', encoding='utf-8') as f:
                    getattr(df, f'to_{args.format}')(f, **format_options[args.format])
            else:
                getattr(df, f'to_{args.format}')(args.output, **format_options[args.format])
        else:
            with pd.option_context('display.max_rows', None):
                print(df)

    if args.database_command:
        locals()[args.database_command.replace('-', '_')]()
    else:
        parser.print_help()

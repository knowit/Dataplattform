import boto3
from botocore.exceptions import ClientError
import os

STAGE = os.environ.get('STAGE', None)


class GlueRepositoryException(Exception):
    pass


class GlueRepositoryNotFoundException(Exception):
    pass


class GlueRepositoryBase:
    def __init__(self):
        self.client = boto3.client('glue')


class DatabaseRepository(GlueRepositoryBase):
    ignore_databases = ['default']

    def get(self, database_name: str):
        try:
            db = self.client.get_database(Name=f'{STAGE}_{database_name}' if STAGE else database_name)
            if db['Database']['Name'] in self.ignore_databases:
                raise GlueRepositoryNotFoundException('Not found')
            return {
                **db['Database'],
                'Name': db['Database']['Name'].lstrip(f'{STAGE}_'),
                '_Name': db['Database']['Name']
            }
        except ClientError as error:
            if error.response['Error']['Code'] == 'EntityNotFoundException':
                raise GlueRepositoryNotFoundException(error.response['Error']['Message'])
            else:
                raise GlueRepositoryException(error.response['Error']['Message'])

    def all(self):
        paginator = self.client.get_paginator('get_databases')
        try:
            response_iterator = paginator.paginate()
            return [
                {**db, 'Name': db['Name'].lstrip(f'{STAGE}_'), '_Name': db['Name']}
                for resp in response_iterator for db in resp['DatabaseList']
                if db['Name'] not in self.ignore_databases
            ]
        except ClientError as error:
            raise GlueRepositoryException(error.response['Error']['Message'])


class TableRepository(GlueRepositoryBase):
    def get(self, database_name: str, table_name: str):
        try:
            table = self.client.get_table(
                DatabaseName=f'{STAGE}_{database_name}' if STAGE else database_name,
                Name=table_name)
            return {**table['Table'], 'DatabaseName': table['Table']['DatabaseName'].lstrip(f'{STAGE}_')}
        except ClientError as error:
            if error.response['Error']['Code'] == 'EntityNotFoundException':
                raise GlueRepositoryNotFoundException(error.response['Error']['Message'])
            else:
                raise GlueRepositoryException(error.response['Error']['Message'])

    def all(self, database_name: str):
        paginator = self.client.get_paginator('get_tables')
        try:
            response_iterator = paginator.paginate(DatabaseName=f'{STAGE}_{database_name}' if STAGE else database_name)
            return [
                {**table, 'DatabaseName': table['DatabaseName'].lstrip(f'{STAGE}_')}
                for resp in response_iterator for table in resp['TableList']
            ]
        except ClientError as error:
            raise GlueRepositoryException(error.response['Error']['Message'])

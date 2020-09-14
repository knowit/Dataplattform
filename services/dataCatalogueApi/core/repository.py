import boto3
from botocore.exceptions import ClientError


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
            db = self.client.get_database(Name=database_name)
            if (db['Database']['Name'] in self.ignore_databases):
                raise GlueRepositoryNotFoundException('Not found')
            return {**db['Database'], 'Name': db['Database']['Name'].lstrip('dev_')}
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
                {**db, 'Name': db['Name'].lstrip('dev_')} for resp in response_iterator for db in resp['DatabaseList']
                if db['Name'] not in self.ignore_databases
            ]
        except ClientError as error:
            raise GlueRepositoryException(error.response['Error']['Message'])


class TableRepository(GlueRepositoryBase):
    def get(self, database_name: str, table_name: str):
        try:
            table = self.client.get_table(DatabaseName=database_name, Name=table_name)
            return table['Table']
        except ClientError as error:
            if error.response['Error']['Code'] == 'EntityNotFoundException':
                raise GlueRepositoryNotFoundException(error.response['Error']['Message'])
            else:
                raise GlueRepositoryException(error.response['Error']['Message'])

    def all(self, database_name: str):
        paginator = self.client.get_paginator('get_tables')
        try:
            response_iterator = paginator.paginate(DatabaseName=database_name)
            return [
                db for resp in response_iterator for db in resp['TableList']
            ]
        except ClientError as error:
            raise GlueRepositoryException(error.response['Error']['Message'])

import boto3
import os

STAGE = os.environ.get('STAGE', None)


class GlueRepositoryNotFoundException(Exception):
    pass


class GlueRepositoryBase:
    def __init__(self):
        self.client = boto3.client('glue')


class DatabaseRepository(GlueRepositoryBase):
    ignore_databases = ['default']

    def get(self, database_name: str):
        db = self.client.get_database(Name=f'{STAGE}_{database_name}' if STAGE else database_name)
        if db['Database']['Name'] in self.ignore_databases:
            raise GlueRepositoryNotFoundException('Not found')
        return {
            **db['Database'],
            'Name': db['Database']['Name'].lstrip(f'{STAGE}_'),
            '_Name': db['Database']['Name']
        }

    def all(self):
        paginator = self.client.get_paginator('get_databases')
        response_iterator = paginator.paginate()

        return [
            {**db, 'Name': db['Name'].lstrip(f'{STAGE}_'), '_Name': db['Name']}
            for resp in response_iterator for db in resp['DatabaseList']
            if db['Name'] not in self.ignore_databases
        ]


class TableRepository(GlueRepositoryBase):
    def get(self, database_name: str, table_name: str):
        table = self.client.get_table(
            DatabaseName=f'{STAGE}_{database_name}' if STAGE else database_name,
            Name=table_name)
        return {**table['Table'], 'DatabaseName': table['Table']['DatabaseName'].lstrip(f'{STAGE}_')}

    def all(self, database_name: str):
        paginator = self.client.get_paginator('get_tables')
        response_iterator = paginator.paginate(DatabaseName=f'{STAGE}_{database_name}' if STAGE else database_name)

        return [
            {**table, 'DatabaseName': table['DatabaseName'].lstrip(f'{STAGE}_')}
            for resp in response_iterator for table in resp['TableList']
        ]

import os
from botocore.exceptions import ClientError
from dataplattform.common.aws import Glue

STAGE = os.environ.get('STAGE', None)


class GlueRepositoryException(Exception):
    pass


class GlueRepositoryNotFoundException(Exception):
    pass


class GlueRepositoryBase:
    def __init__(self):
        self.glue = Glue(ignore_databases=['default'])


class DatabaseRepository(GlueRepositoryBase):

    def get(self, database_name: str):
        try:
            db = self.glue.get_database(f'{STAGE}_{database_name}' if STAGE else database_name)
            return {
                **db,
                'Name': db['Name'].lstrip(f'{STAGE}_'),
                '_Name': db['Name']
            }
        except Glue.DatabaseIgnoredException:
            raise GlueRepositoryNotFoundException('Not found')
        except ClientError as error:
            if error.response['Error']['Code'] == 'EntityNotFoundException':
                raise GlueRepositoryNotFoundException(error.response['Error']['Message'])
            else:
                raise GlueRepositoryException(error.response['Error']['Message'])

    def all(self):
        try:
            databases = self.glue.get_databases()
            return [
                {**db, 'Name': db['Name'].lstrip(f'{STAGE}_'), '_Name': db['Name']}
                for db in databases
            ]
        except ClientError as error:
            raise GlueRepositoryException(error.response['Error']['Message'])


class TableRepository(GlueRepositoryBase):
    def get(self, database_name: str, table_name: str):
        try:
            table = self.glue.get_table(table_name, f'{STAGE}_{database_name}' if STAGE else database_name)
            return {**table['Table'], 'DatabaseName': table['Table']['DatabaseName'].lstrip(f'{STAGE}_')}
        except Glue.DatabaseIgnoredException:
            raise GlueRepositoryNotFoundException('Not Found')
        except ClientError as error:
            if error.response['Error']['Code'] == 'EntityNotFoundException':
                raise GlueRepositoryNotFoundException(error.response['Error']['Message'])
            else:
                raise GlueRepositoryException(error.response['Error']['Message'])

    def all(self, database_name: str):
        try:
            tables = self.glue.get_tables(f'{STAGE}_{database_name}' if STAGE else database_name)
            return [
                {**table, 'DatabaseName': table['DatabaseName'].lstrip(f'{STAGE}_')}
                for table in tables
            ]
        except ClientError as error:
            raise GlueRepositoryException(error.response['Error']['Message'])

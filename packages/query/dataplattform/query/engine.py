from pyathena import connect
from pyathena.pandas_cursor import PandasCursor
from os import environ, path, sep
from pypika import Table
from typing import Union, AnyStr, Dict, Any
from dataplattform.query.ext import Query, QueryBuilder


class Athena:
    def __init__(self,
                 staging_dir: str = None,
                 bucket: str = None,
                 access_path: str = None,
                 default_database: str = None):

        default_staging_dir = path.join(
            bucket or environ.get('DATALAKE'),
            access_path or environ.get('ACCESS_PATH'),
            'stage').replace(sep, '/')

        self.staging_dir = staging_dir or environ.get(
                'STAGING_DIR', f"s3://{default_staging_dir}")
        self.default_database = Athena.database_name(
            default_database or environ.get('DEFAULT_DATABASE', None))
        self.__connection = None

    @property
    def connection(self):
        self.__connection = self.__connection or connect(
            s3_staging_dir=self.staging_dir,
            cursor_class=PandasCursor)
        return self.__connection

    @property
    def table(self):
        class TableFactory:
            def __init__(self, database: str):
                self.tables = {}
                self.database = database or ''

            def __getitem__(self, key):
                key = key if '.' in key else f'{self.database}.{key}'
                schema, table_name = key.split('.')
                self.tables[key] = self.tables.get(
                    key,
                    Table(table_name, schema=Athena.database_name(schema), query_cls=Query))
                return self.tables[key]

            def __getattr__(self, key):
                return self[key]

        self.factory = getattr(self, 'factory', TableFactory(self.default_database))
        return self.factory

    def execute(self, query: Union[QueryBuilder, AnyStr], parameters: Dict[AnyStr, Any] = None):
        cursor = self.connection.cursor()
        if hasattr(query, 'get_sql'):
            return cursor.execute(query.get_sql())
        return cursor.execute(query, parameters=parameters)

    def from_(self, table: Union[Table, AnyStr]):
        if isinstance(table, str):
            table = self.table[table]

        return Query.from_(table)

    @staticmethod
    def database_name(name: str):
        if not name:
            return None
        prefix = f'{environ.get("STAGE")}_' if not name.startswith(environ.get('STAGE')) else ''
        postfix = '_database' if not name.endswith('database') else ''
        return ''.join([prefix, name, postfix])

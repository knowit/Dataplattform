from dataplattform.common.aws import S3, SNS, GlueCrawler
from dataplattform.common.handlers import Response, verify_schema, make_wrapper_func
from dataplattform.common.repositories.person_repository import PersonRepository, PersonIdentifierType
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, Callable, List, AnyStr
from warnings import catch_warnings, filterwarnings
from os import environ

with catch_warnings():
    filterwarnings("ignore")
    from fastparquet import ParquetFile


def ensure_partitions_has_values(frame: pd.DataFrame, table_partitions: List[AnyStr]):
    for partition in table_partitions:
        if np.issubdtype(frame[partition].dtype, np.number):
            frame.loc[frame[partition].isnull(), partition] = -1
        else:
            frame.loc[frame[partition].isnull(), partition] = 'undefined'
    return frame


def check_exists(s3: S3, frame: pd.DataFrame, table_name: str, table_partitions: List[AnyStr]):
    table_exists = s3.fs.exists(f'structured/{table_name}/_metadata')
    if table_exists:
        dataset = ParquetFile(f'structured/{table_name}', open_with=s3.fs.open)
        if not verify_schema(dataset, frame, table_partitions):
            old_files = [
                fn.split(f'structured/{table_name}/')[-1]
                for fn in s3.fs.find(f'structured/{table_name}')
            ]
            deprecation_date = datetime.now().replace(microsecond=0).isoformat()
            for old_file in old_files:
                s3.fs.copy(f'structured/{table_name}/{old_file}',
                           f'structured/deprecated/{deprecation_date}/{table_name}/{old_file}')

            s3.fs.rm(f'structured/{table_name}', recursive=True)
            table_exists = False
    return table_exists


def delete_table(s3: S3, table_name: str):
    table_exists = s3.fs.exists(f'structured/{table_name}/_metadata')
    if table_exists:
        s3.fs.rm(f'structured/{table_name}', recursive=True)


class ProcessHandler:
    def __init__(self, access_path: str = None, bucket: str = None):
        self.access_path = access_path
        self.bucket = bucket
        self.wrapped_func: Dict[str, Callable] = {}
        self.wrapped_func_args: Dict[str, Any] = {}
        self.s3 = S3(
            access_path=access_path,
            bucket=bucket)

    def __call__(self, event, context=None):
        assert 'process' in self.wrapped_func, \
            'ProcessHandler must wrap a process function'

        s3_data = self.get_s3_data(event)

        updated_tables = self.update_tables(
            *self.call_wrapped(s3_data, event)
        )

        self.send_data_update_message(updated_tables)

        return Response().to_dict()

    def get_s3_data(self, event):
        return [
            self.s3.get(key) for key in
            [
                record.get('body', None) for record in event.get('Records', [])
            ] if key
        ]

    def call_wrapped(self, s3_data, event):
        data = self.wrapped_func['process'](s3_data, event.get('Records', []))
        partitions = self.wrapped_func_args.get('process', {}).get('partitions', {})
        overwrite = self.wrapped_func_args.get('process', {}).get('overwrite', False)

        return data, partitions, overwrite

    def update_tables(self, tables, partitions, overwrite):
        updated_tables = []

        for table_name, frame in tables.items():
            if frame is None:
                continue

            assert isinstance(frame, pd.DataFrame), \
                'Process must return a DataFrame'

            if frame.empty:
                continue

            table_partitions = partitions.get(table_name, [])
            frame = ensure_partitions_has_values(frame, table_partitions)

            table_exists = check_exists(self.s3, frame, table_name, table_partitions)

            if table_exists and overwrite:
                delete_table(self.s3, table_name)
                table_exists = False

            frame.to_parquet(f'structured/{table_name}',
                             engine='fastparquet',
                             compression='GZIP',
                             index=False,
                             partition_cols=table_partitions,
                             file_scheme='hive',
                             mkdirs=lambda x: None,  # noop
                             open_with=self.s3.fs.open,
                             append=table_exists)

            glue = GlueCrawler()
            glue.update_crawler(table_name)

            updated_tables.append(table_name)

        return updated_tables

    def send_data_update_message(self, updated_tables):
        sns = SNS(environ.get('DATA_UPDATE_TOPIC'))
        sns.publish({'tables': updated_tables}, 'DataUpdate')
        return True

    def process(self, partitions, overwrite=False):
        def wrap(f):
            self.wrapped_func['process'] = make_wrapper_func(f, dict)
            self.wrapped_func_args['process'] = dict(partitions=partitions, overwrite=overwrite)
            return self.wrapped_func['process']

        return wrap


class PersonDataProcessHandler(ProcessHandler):
    def __init__(self, id_type: PersonIdentifierType, access_path=None, bucket=None) -> None:
        super().__init__(access_path=access_path, bucket=bucket)
        self.id_type = id_type

    def call_wrapped(self, s3_data, event):
        data, partitions, overwrite = super().call_wrapped(s3_data, event)

        pdtables = self.wrapped_func_args.get('process', {}).get('person_data_tables', [])

        for table_name in pdtables:
            frame = data[table_name]

            assert self.id_type.value in frame, \
                f"id column {self.id_type.name} missing on table {table_name}"

            with PersonRepository() as repo:
                frame["guid"] = frame[self.id_type.value].transform(lambda v: repo.get_guid_by(self.id_type, v))

            del frame[self.id_type.value]

            table_partition = partitions.get(table_name, [])

            if "guid" not in table_partition:
                table_partition.insert(0, "guid")

            if self.id_type.value in table_partition:
                table_partition.remove(self.id_type.value)

            partitions[table_name] = table_partition

        return data, partitions, overwrite

    def process(self, partitions, person_data_tables: List[str], overwrite=False):
        def wrap(f):
            self.wrapped_func['process'] = make_wrapper_func(f, dict)
            self.wrapped_func_args['process'] = dict(
                partitions=partitions,
                overwrite=overwrite,
                person_data_tables=person_data_tables
            )
            return self.wrapped_func['process']

        return wrap

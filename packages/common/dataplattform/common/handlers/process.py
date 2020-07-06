from dataplattform.common.schema import Data
from dataplattform.common.aws import S3
from dataplattform.common.handlers import Response
from fastparquet import ParquetFile
from datetime import datetime
import numpy as np
from typing import Dict, Any, Callable


class ProcessHandler:
    def __init__(self, access_path: str = None, bucket: str = None):
        self.access_path = access_path
        self.bucket = bucket
        self.wrapped_func: Dict[str, Callable]  = {}
        self.wrapped_func_args: Dict[str, Any] = {}

    def __call__(self, event, context=None):
        s3 = S3(
            access_path=self.access_path,
            bucket=self.bucket)

        def load_event_data(event):
            keys = [record.get('messageAttributes', {}).get('s3FileName', {}).get('stringValue', '')
                    for record in event.get('Records', [])
                    ]
            sent_time_list = [record.get('attributes', {}).get('SentTimestamp', 0)
                                for record in event.get('Records', [])
                                ]

            recieved_time_list = [record.get('attributes', {}).get('ApproximateFirstReceiveTimestamp', 0)
                                    for record in event.get('Records', [])
                                    ]

            keylist = [s3.get(key) for key in keys if key]
            return [keylist, sent_time_list, recieved_time_list]  # TODO: Fix

        data = load_event_data(event)
        if data:
            tables = self.wrapped_func['process'](data)
            partitions = self.wrapped_func_args.get('process', {}).get('partitions', {})

            for table_name, frame in tables.items():
                if frame is None:
                    continue

                assert frame is not None and callable(frame.to_parquet),\
                    'Process must return a DataFrame with a to_parquet method'

                if frame.empty:
                    continue

                table_partitions = partitions.get(table_name, [])

                for partition in table_partitions:
                    if np.issubdtype(frame[partition].dtype, np.number):
                        frame.loc[frame[partition].isnull(), partition] = -1
                    else:
                        frame.loc[frame[partition].isnull(), partition] = 'undefined'

                table_exists = s3.fs.exists(f'structured/{table_name}/_metadata')
                if table_exists:
                    dataset = ParquetFile(f'structured/{table_name}', open_with=s3.fs.open)
                    if not ProcessHandler.verify_schema(dataset, frame, table_partitions):
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

                frame.to_parquet(f'structured/{table_name}',
                                    engine='fastparquet',
                                    compression='GZIP',
                                    index=False,
                                    partition_cols=table_partitions,
                                    file_scheme='hive',
                                    mkdirs=lambda x: None,  # noop
                                    open_with=s3.fs.open,
                                    append=table_exists)

        return Response().to_dict()


    def process(self, partitions):
        def wrap(f):
            self.wrapped_func['process'] = ProcessHandler.__wrapper_func(f, dict)
            self.wrapped_func_args['process'] = dict(partitions=partitions)
            return self.wrapped_func['process']
        return wrap

    @staticmethod
    def verify_schema(dataset: ParquetFile, dataframe, partitions):
        dataset_partitions = dataset.info.get('partitions', [])
        dataset_columns = dataset.columns + dataset_partitions

        if len(dataset_partitions) != len(partitions):
            return False

        if not all([a == b for a, b in zip(sorted(dataset_partitions), sorted(partitions))]):
            return False

        if len(dataset_columns) != len(dataframe.columns):
            return False

        if not all([a == b for a, b in zip(sorted(dataset_columns), sorted(dataframe.columns))]):
            return False

        if not all([dataset.dtypes[c] == dataframe.dtypes[c] for c in dataset.columns]):
            return False

        return True

    @staticmethod
    def __wrapper_func(f, *return_type):
        def func(event):
            result = f(event)
            assert result is None or any([isinstance(result, t) for t in return_type]),\
                f'Return type {type(result).__name__} must be None or\
                    any {", ".join([t.__name__ for t in return_type])}'
            return result
        return func

from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
from dataplattform.common.schema import Data
from dataplattform.common.aws import S3, S3Result
from fastparquet import ParquetFile
from datetime import datetime


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Response:
    status_code: int = 200
    body: str = ''


class Handler:
    def __init__(self, access_path: str = None, bucket: str = None):
        self.access_path = access_path
        self.bucket = bucket
        self.wrapped_func = {}
        self.wrapped_func_args = {}

    def __call__(self, event, context=None):
        if 'validate' in self.wrapped_func:
            result = self.wrapped_func['validate'](event)
            if result and isinstance(result, Response):
                return result.to_dict()

            if result is False:
                return Response(status_code=403).to_dict()

            if result and isinstance(result, str):
                return Response(status_code=403, body=result).to_dict()

        s3 = S3(
            access_path=self.access_path,
            bucket=self.bucket)
        raw_data = None

        if 'ingest' in self.wrapped_func:
            result = self.wrapped_func['ingest'](event)
            if result and isinstance(result, Response):
                return result.to_dict()

            if result:
                raw_data = result
                s3.put(raw_data, 'raw')

        if 'process' in self.wrapped_func:
            def load_event_data(event):
                keys = [
                    r.get('s3', {}).get('object', {}).get('key', None)
                    for r in event.get('Records', [])
                ]
                return [s3.get(key) for key in keys if key]

            data = [S3Result(raw_data)] if raw_data else load_event_data(event)
            if data:
                tables = self.wrapped_func['process'](data)
                partitions = self.wrapped_func_args.get('process', {}).get('partitions', {})

                for table_name, frame in tables.items():
                    if frame is None:
                        continue

                    assert frame is not None and callable(frame.to_parquet),\
                        'Process must return a DataFrame with a to_parquet method'

                    table_partitions = partitions.get(table_name, [])
                    table_exists = s3.fs.exists(f'structured/{table_name}/_metadata')
                    if table_exists:
                        dataset = ParquetFile(f'structured/{table_name}', open_with=s3.fs.open)
                        if not Handler.verify_schema(dataset, frame, table_partitions):
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

    def validate(self):
        def wrap(f):
            self.wrapped_func['validate'] = Handler.__wrapper_func(f, bool, str, Response)
            return self.wrapped_func['validate']
        return wrap

    def ingest(self):
        def wrap(f):
            self.wrapped_func['ingest'] = Handler.__wrapper_func(f, Data, Response)
            return self.wrapped_func['ingest']
        return wrap

    def process(self, partitions):
        def wrap(f):
            self.wrapped_func['process'] = Handler.__wrapper_func(f, dict)
            self.wrapped_func_args['process'] = dict(partitions=partitions)
            return self.wrapped_func['process']
        return wrap

    @staticmethod
    def verify_schema(dataset: ParquetFile, dataframe, partitions):
        dataset_partitions = dataset.info.get('partitions', [])
        if len(dataset_partitions) != len(partitions):
            return False

        if not all([a == b for a, b in zip(sorted(dataset_partitions), sorted(partitions))]):
            return False

        if len(dataset.columns) != len(dataframe.columns):
            return False

        if not all([a == b for a, b in zip(sorted(dataset.columns), sorted(dataframe.columns))]):
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

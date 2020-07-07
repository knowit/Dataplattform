from dataplattform.common.schema import Data
from dataplattform.common.aws import S3, S3Result
from dataplattform.common.handlers import Response, make_wrapper_func
from dataplattform.common.handlers.process import check_exists, ensure_partitions_has_values
from typing import Dict, Any, Callable
from warnings import warn


class MixedHandler:
    def __init__(self, access_path: str = None, bucket: str = None):
        warn('MixedHandler is deprecated: use separate ingest and process handlers', DeprecationWarning)

        self.access_path = access_path
        self.bucket = bucket
        self.wrapped_func: Dict[str, Callable] = {}
        self.wrapped_func_args: Dict[str, Any] = {}

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

                    if frame.empty:
                        continue

                    table_partitions = partitions.get(table_name, [])
                    frame = ensure_partitions_has_values(frame, table_partitions)

                    table_exists = check_exists(s3, frame, table_name, table_partitions)

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
            self.wrapped_func['validate'] = make_wrapper_func(f, bool, str, Response)
            return self.wrapped_func['validate']
        return wrap

    def ingest(self):
        def wrap(f):
            self.wrapped_func['ingest'] = make_wrapper_func(f, Data, Response)
            return self.wrapped_func['ingest']
        return wrap

    def process(self, partitions):
        def wrap(f):
            self.wrapped_func['process'] = make_wrapper_func(f, dict)
            self.wrapped_func_args['process'] = dict(partitions=partitions)
            return self.wrapped_func['process']
        return wrap

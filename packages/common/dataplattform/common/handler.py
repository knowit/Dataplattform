from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
from dataplattform.common.schema import Data
from dataplattform.common.aws import S3


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Response:
    status_code: int = 200
    body: str = ''


class Handler:
    class Wrapper:
        def __init__(self, fallback=None):
            self.fallback = fallback

        def __setitem__(self, name, value):
            self.__dict__[name] = value

        def __getitem__(self, name):
            return self.__dict__[name] if name in self.__dict__ else self.fallback

        def __getattr__(self, name):
            return self[name]

    def __init__(self):
        self.wrapped = Handler.Wrapper(lambda x: None)
        self.wrapped_args = Handler.Wrapper()

    def __call__(self, event, context=None):
        return self.run(event, context)

    def make_wrapper(self, name, *return_types):
        def wrapper(**kwargs):
            self.wrapped_args[name] = kwargs

            def wrap(f):
                self.wrapped[name] = Handler.__wrapper_func(f, *return_types)
                return self.wrapped[name]
            return wrap
        self.__dict__[name] = wrapper

    def run(self, event, context=None):
        raise NotImplementedError

    @staticmethod
    def __wrapper_func(f, *return_type):
        def func(event):
            result = f(event)
            assert result is None or not return_type or any([isinstance(result, t) for t in return_type]),\
                f'Return type {type(result).__name__} must be None or\
                    any {", ".join([t.__name__ for t in return_type])}'
            return result
        return func


def ingestion(access_path: str = None, bucket: str = None):
    class IngestionHandler(Handler):
        def __init__(self):
            super().__init__()
            self.make_wrapper('validate', bool, str, Response)
            self.make_wrapper('ingest', Data, Response)

        def run(self, event, context=None):
            result = self.wrapped.validate(event)
            if result and isinstance(result, Response):
                return result.to_dict()

            if result is False:
                return Response(status_code=403).to_dict()

            if result and isinstance(result, str):
                return Response(status_code=403, body=result).to_dict()

            result = self.wrapped.ingest(event)
            if result and isinstance(result, Response):
                return result.to_dict()

            if result:
                S3(
                    access_path=access_path,
                    bucket=bucket
                ).put(result)

            return Response().to_dict()

    return IngestionHandler()


def processor(access_path: str = None, bucket: str = None):
    def load_event_data(event):
        s3 = S3(access_path=access_path, bucket=bucket)
        keys = [
            r.get('s3', {}).get('object', {}).get('key', None)
            for r in event.get('Records', [])
        ]
        return [s3.get(key) for key in keys if key]

    class ProcessorHandler(Handler):
        def __init__(self):
            super().__init__()
            self.make_wrapper('process', dict)

        def run(self, event, context=None):
            data = load_event_data(event)
            if not data:
                return Response().to_dict()

            tables = self.wrapped.process(data)
            for table_name, frame in tables.items():
                assert frame is not None and callable(frame.to_parquet),\
                    'Process must return a DataFrame with a to_parquet method'

                partitions = self.wrapped_args.process['partitions'] \
                    if 'partitions' in self.wrapped_args.process else None

                s3fs = S3(access_path=access_path, bucket=bucket).simple_fs
                frame.to_parquet(f'database/{table_name}',
                                 engine='fastparquet',
                                 compression='gzip',
                                 index=False,
                                 partition_cols=partitions,
                                 file_scheme='hive',
                                 mkdirs=lambda x: None,
                                 open_with=s3fs.open,
                                 append=s3fs.exists(f'database/{table_name}/_metadata'))

            return Response().to_dict()

    return ProcessorHandler()

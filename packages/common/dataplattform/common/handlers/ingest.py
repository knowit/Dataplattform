from dataplattform.common.schema import Data
from dataplattform.common.aws import S3, SQS
from dataplattform.common.handlers import Response, make_wrapper_func
from typing import Dict, Any, Callable


class IngestHandler:
    def __init__(self, access_path: str = None, access_path_strict: str = None, bucket: str = None):
        self.access_path = access_path
        self.access_path_strict = access_path_strict
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
        if self.access_path_strict: # todo double check med whitespaces n shit
            s3 = S3(
                access_path=self.access_path_strict,
                bucket=self.bucket
            )
        print(f'S3 access_path be: {s3.access_path}') # todo slett print
        assert 'ingest' in self.wrapped_func, \
            'IngestHandler must wrap and ingest function'

        result = self.wrapped_func['ingest'](event)
        overwrite = self.wrapped_func_args.get('ingest', {}).get('overwrite', False)
        if result and isinstance(result, Response):
            return result.to_dict()

        if result:
            if overwrite:
                s3.empty_content_in_path('raw', delete_all_versions=True)
            SQS().send_custom_filename_message(
                s3.put(result, 'raw'))

        return Response().to_dict()

    def validate(self):
        def wrap(f):
            self.wrapped_func['validate'] = make_wrapper_func(
                f, bool, str, Response)
            return self.wrapped_func['validate']
        return wrap

    def ingest(self, overwrite=False):
        def wrap(f):
            self.wrapped_func['ingest'] = make_wrapper_func(f, Data, Response)
            self.wrapped_func_args['ingest'] = dict(overwrite=overwrite)
            return self.wrapped_func['ingest']
        return wrap

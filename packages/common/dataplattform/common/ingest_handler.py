from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
from dataplattform.common.schema import Data
from dataplattform.common.aws import S3, SQS


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

        sqs = SQS()

        if 'ingest' in self.wrapped_func:
            result = self.wrapped_func['ingest'](event)
            if result and isinstance(result, Response):
                return result.to_dict()

            if result:
                raw_data = result
                response = sqs.send_message(s3.put(raw_data, 'raw'))
                assert response.get('Failed') is None

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

    @staticmethod
    def __wrapper_func(f, *return_type):
        def func(event):
            result = f(event)
            assert result is None or any([isinstance(result, t) for t in return_type]),\
                f'Return type {type(result).__name__} must be None or\
                    any {", ".join([t.__name__ for t in return_type])}'
            return result
        return func

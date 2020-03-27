from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
from dataplattform.common.schema import Data
from dataplattform.common.aws import S3


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Response:
    status_code: int = 200
    body: str = ''


def ingestion(access_path: str = None, bucket: str = None):
    class Handler:
        def __call__(self, event, context=None):
            if 'validate_func' in dir(self):
                result = self.validate_func(event)
                if result is not None:
                    return result.to_dict()

            if 'ingest_func' in dir(self):
                result = self.ingest_func(event)
                if result is not None:
                    S3(
                        access_path=access_path,
                        bucket=bucket
                    ).put(result)

            return Response().to_dict()

        def validate(self):
            def wrap(f):
                self.validate_func = Handler.__wrapper_func(f, Response)
                return self.validate_func
            return wrap

        def ingest(self):
            def wrap(f):
                self.ingest_func = Handler.__wrapper_func(f, Data)
                return self.ingest_func
            return wrap

        @staticmethod
        def __wrapper_func(f, returnType):
            def func(event):
                result = f(event)
                assert result is None or isinstance(result, returnType)
                return result
            return func

    return Handler()

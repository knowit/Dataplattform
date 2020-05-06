import boto3
from os import path, sep, environ
from botocore.exceptions import ClientError
from dataplattform.common.schema import Data
from s3fs import S3FileSystem
from json import loads


class S3Result:
    def __init__(self, res, error=None):
        self.res = res
        self.error = error

    @property
    def raw(self):
        if isinstance(self.res, Data):
            return self.res.to_dict()
        return self.res['Body'].read() if self.res else None

    def json(self, **json_args):
        if isinstance(self.res, Data):
            return self.res.to_dict()
        return loads(self.res['Body'].read(), **json_args) if self.res else None


class S3:
    def __init__(self, access_path: str = None, bucket: str = None):
        self.access_path = access_path or environ.get("ACCESS_PATH")
        self.bucket = bucket or environ.get('DATALAKE')
        self.s3 = boto3.resource('s3')

    def put(self, data: Data, path: str = ''):
        key = path_join(self.access_path, path, f'{int(data.metadata.timestamp)}.json')
        s3_object = self.s3.Object(self.bucket, key)
        s3_object.put(Body=data.to_json().encode('utf-8'))
        return key

    def get(self, key, catch_client_error=True) -> S3Result:
        key = path_join(self.access_path, key) if not key.startswith(self.access_path) else key
        try:
            res = self.s3.Object(self.bucket, key).get()
            return S3Result(res)
        except ClientError as e:
            if not catch_client_error:
                raise e
            return S3Result(None, error=e)

    @property
    def fs(self):
        if 'fs_cache' in self.__dict__:
            return self.fs_cache

        s3 = S3FileSystem(anon=False)

        def get_key(k):
            return path_join(self.bucket, path_join(self.access_path, k) if not k.startswith(self.access_path) else k)

        class S3FSWrapper:
            @staticmethod
            def open(path, *args, **kwargs):
                return s3.open(get_key(path), *args, **kwargs)

            @staticmethod
            def exists(path):
                return s3.exists(get_key(path))

        self.fs_cache = S3FSWrapper()
        return self.fs_cache


class SSM:
    def __init__(self, with_decryption: bool = False, path: str = None):
        self.path = path or path_join('/', environ.get("STAGE"), environ.get("SERVICE"))
        self.with_decryption = with_decryption
        self.client = boto3.client('ssm')

    def get(self, *names):
        if len(names) == 1:
            return next(self.__get(names[0]))
        else:
            return list(self.__get(*names))

    def __get(self, *names):
        for name in names:
            yield self.client.get_parameter(
                Name=path_join('/', self.path, name),
                WithDecryption=self.with_decryption).get('Parameter', {}).get('Value', None)

    def put(self, name, value, value_type, overwrite=False, tier='Standard'):
        self.client.put_parameter(
            Name=path_join('/', self.path, name),
            Value=value,
            Type=value_type,
            Overwrite=overwrite,
            Tier=tier)


def path_join(*paths):
    return path.join(*paths).replace(sep, '/')

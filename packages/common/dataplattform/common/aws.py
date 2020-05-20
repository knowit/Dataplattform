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

        def get_key(k):
            full_access_path = path_join(self.bucket, self.access_path)

            if k.startswith(full_access_path):
                return k
            elif k.startswith(self.access_path):
                return path_join(self.bucket, k)
            else:
                return path_join(full_access_path, k)

        class S3FileSystemProxy(S3FileSystem):
            def open(self, path, *args, **kwargs):
                return S3FileSystem.open(self, get_key(path), *args, **kwargs)

            def exists(self, path):
                return S3FileSystem.exists(self, get_key(path))

            def ls(self, path, **kwargs):
                return S3FileSystem.ls(self, get_key(path), **kwargs)

            def isdir(self, path):
                return S3FileSystem.isdir(self, get_key(path))

            def walk(self, path, *args, **kwargs):
                return S3FileSystem.walk(self, get_key(path), *args, **kwargs)

            def find(self, path, *args, **kwargs):
                return S3FileSystem.find(self, get_key(path), *args, **kwargs)

            def copy(self, path1, path2, **kwargs):
                return S3FileSystem.copy(self, get_key(path1), get_key(path2), **kwargs)

            def rm(self, path, **kwargs):
                return S3FileSystem.rm(self, get_key(path), **kwargs)

        self.fs_cache = S3FileSystemProxy(anon=False)
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
            param = self.client.get_parameter(
                Name=path_join('/', self.path, name),
                WithDecryption=self.with_decryption).get('Parameter', {})
            yield param.get('Value', None) \
                if param.get('Type', '') != 'StringList' \
                else param.get('Value', None).split(',')

    def put(self, name, value, overwrite=True, tier='Standard'):

        self.client.put_parameter(
            Name=path_join('/', self.path, name),
            Value=value,
            Type='String' if (self.with_decryption is False)
                 else 'SecureString',
            Overwrite=overwrite,
            Tier=tier)


def path_join(*paths):
    return path.join(*paths).replace(sep, '/')

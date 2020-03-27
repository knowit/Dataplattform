from os import environ
import boto3
from os import path, sep
from dataplattform.common.schema import Data


class S3:
    def __init__(self, access_path: str = None, bucket: str = None):
        self.access_path = access_path or environ.get("ACCESS_PATH")
        self.bucket = bucket or environ.get('DATALAKE')
        self.s3 = boto3.resource('s3')

    def put(self, data: Data):
        s3_object = self.s3.Object(self.bucket, path_join(self.access_path, f'{int(data.metadata.timestamp)}.json'))
        s3_object.put(Body=data.to_json().encode('utf-8'))


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


def path_join(*paths):
    return path.join(*paths).replace(sep, '/')

import boto3
from os import path, sep, environ
from botocore.exceptions import ClientError
from dataplattform.common.schema import Data
from s3fs import S3FileSystem
from json import loads, dumps
from uuid import uuid4


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


class Glue:
    def __init__(self, access_level=None, access_path=None):
        self.access_level = access_level or environ.get('ACCESS_LEVEL')
        self.access_path = access_path or environ.get('ACCESS_PATH')
        self.bucket = environ.get('DATALAKE')
        self.stage = environ.get('STAGE')
        self.glue = boto3.client('glue')
        self.crawler_name = f'{self.stage}_level_{self.access_level[-1]}_crawler'

    def get_crawler(self):
        try:
            res = self.glue.get_crawler(Name=self.crawler_name)
            return res
        except ClientError:
            return None

    def update_crawler(self, table_name):
        crawler_metadata = self.get_crawler()
        if crawler_metadata is not None:
            current_targets = crawler_metadata.get('Crawler', {}).get('Targets', {}).get('S3Targets', [])
            path = f's3://{self.bucket}/{self.access_path}structured/{table_name}'

            if path not in [target.get('Path', None) for target in current_targets]:
                targets = [*current_targets, {
                        'Path': path,
                        'Exclusions': ['*_metadata']
                    }
                ]
                # Will not update if crawler is running
                try:
                    self.glue.update_crawler(
                        Name=self.crawler_name,
                        Targets={'S3Targets': targets},
                    )
                except ClientError as e:
                    print(e)

    def start(self):
        try:
            self.glue.start_crawler(Name=self.crawler_name)
        except ClientError as e:
            raise e


class S3:
    def __init__(self, access_path: str = None, bucket: str = None):
        self.access_path = environ.get("ACCESS_PATH") if access_path is None else access_path
        self.bucket = bucket or environ.get('DATALAKE')
        self.s3 = boto3.resource('s3')

    def put(self, data: Data, path: str = ''):
        data_json = data.to_json().encode('utf-8')
        return self.put_raw(data_json, ext='json', path=path)

    def put_raw(self, data: bytes, ext: str = '', path: str = '', key: str = None):
        if data is not None:
            if key is None:
                key = path_join(self.access_path, path, f'{uuid4()}.{ext}')
            else:
                key = path_join(self.access_path, path, key)
            s3_object = self.s3.Object(self.bucket, key)
            s3_object.put(Body=data)
            return key
        return None

    def get(self, key, catch_client_error=True) -> S3Result:
        key = path_join(self.access_path, key) if not key.startswith(self.access_path) else key
        try:
            res = self.s3.Object(self.bucket, key).get()
            return S3Result(res)
        except ClientError as e:
            if not catch_client_error:
                raise e
            return S3Result(None, error=e)

    # Filter is used to be able to specify the files that you wish to delete and keep the rest, handle with care.
    def empty_content_in_path(self, path, delete_all_versions=False, filter_val=None):
        prefix = path_join(self.access_path, path)
        bucket = self.s3.Bucket(self.bucket)
        if delete_all_versions:
            objects_to_be_deleted = bucket.object_versions.filter(Prefix=prefix)
        else:
            objects_to_be_deleted = bucket.objects.filter(Prefix=prefix)

        if filter_val is not None:
            for obj in objects_to_be_deleted:
                if filter_val in obj.key:
                    self.fs.rm(obj.key)
        else:
            objects_to_be_deleted.delete()

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
            yield param.get('Value', None).strip() \
                if param.get('Type', '') != 'StringList' \
                else list(map(str.strip, param.get('Value', None).split(',')))

    def put(self, name, value, overwrite=True, tier='Standard'):

        self.client.put_parameter(
            Name=path_join('/', self.path, name),
            Value=value,
            Type='String' if (self.with_decryption is False)
                 else 'SecureString',
            Overwrite=overwrite,
            Tier=tier)


class SQS:
    def __init__(self):
        self.client = boto3.client('sqs')

    def send_custom_filename_message(self, file_name: str = None, queue_name: str = None, group_id: str = None):
        response = self.client.get_queue_url(QueueName=queue_name or environ.get("SQS_QUEUE_NAME"))
        sqs_url = response['QueueUrl']
        res = self.client.send_message(
            QueueUrl=sqs_url,
            MessageBody=file_name,
            MessageAttributes={
                's3FileName': {
                    'StringValue': file_name,
                    'DataType': 'String'
                }
            },
            MessageGroupId=group_id or environ.get("SQS_MESSAGE_GROUP_ID"))
        return res['MessageId']


class SNS:
    def __init__(self, topicarn: str):
        self.sns = boto3.resource('sns')
        self.topic = self.sns.Topic(topicarn)

    def publish(self, message: dict, subject: str):
        self.topic.publish(
            Message=dumps(message),
            Subject=subject)


def path_join(*paths):
    return path.join(*paths).replace(sep, '/')

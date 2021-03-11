import boto3
from dataplattform.common.aws import S3
from os import environ
from json import dumps


def launch_async_lambda(payload: bytes, lambda_name: str = None):
    download_lambda = boto3.client('lambda')
    download_lambda.invoke(FunctionName=lambda_name,
                           InvocationType='Event',
                           Payload=payload)


def save_document(http_request, filename, filetype, private=True):
    event = {}

    event['body'] = http_request
    event['filename'] = filename
    event['filetype'] = filetype
    event['private'] = private
    launch_async_lambda(dumps(event), environ.get('DOWNLOAD_LAMBDA'))


def empty_content_in_path(bucket, prefix, delete_all_versions=False, filter_val=None):
    s3 = S3(bucket=bucket, access_path='')
    s3.empty_content_in_path(path=prefix, delete_all_versions=delete_all_versions, filter_val=filter_val)

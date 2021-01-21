import boto3
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


def empty_content_in_path(bucket, prefix):
    s3 = boto3.resource('s3')
    s3_bucket = s3.Bucket(bucket)
    s3_bucket.objects.filter(Prefix=prefix).delete()

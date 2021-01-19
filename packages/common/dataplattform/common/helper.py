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
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if 'Contents' in response:
        for obj in response['Contents']:
            s3_client.delete_object(Bucket=bucket, Key=obj['Key'])

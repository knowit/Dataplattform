from dataplattform.common.raw_storage import write_file_to_bucket
import boto3
from urllib import request
from os import environ
from json import dumps


def launch_async_lambda(payload: bytes, lambda_name: str = None):
    download_lambda = boto3.client('lambda')
    download_lambda.invoke(FunctionName=lambda_name,
                           InvocationType='Event',
                           Payload=payload)


def download_from_http(http_request):
    url = http_request.get('requestUrl')
    headers = http_request.get('header', {})
    filetype = http_request.get('filetype')

    valid_content_types = {'pdf':  'application/pdf',
                           'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           'jpg':  'image/jpeg'}

    if filetype not in list(valid_content_types.keys()):
        return 400

    req = request.Request(url)
    for (header, value) in headers.items():
        req.add_header(header, value)

    private = http_request.get('private', True)
    if private:
        bucket = environ.get('PRIVATE_BUCKET')
    else:
        bucket = environ.get('PUBLIC_BUCKET')

    response = request.urlopen(req)
    content_type = response.getheader('Content-Type')
    if content_type == valid_content_types[filetype]:
        if (response.status == 200 and response.readable()):
            write_file_to_bucket(data=response.read(),
                                 filename=http_request['filename'],
                                 bucket=bucket)
        else:
            return 400
    else:
        return 400
    return response.status


def save_document(http_request):
    event = {}
    event['body'] = http_request
    launch_async_lambda(dumps(event), environ.get('DOWNLOAD_LAMBDA'))
    return http_request['filename']

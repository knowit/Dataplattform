from dataplattform.common.aws import S3
from os import environ


def write_to_private_bucket(data: bytes):
    access_path = 'private/' + environ.get('SERVICE')
    s3 = S3(access_path, environ.get('PRIVATE_BUCKET'))
    print(s3.put(data))
    return s3.put(data)


def write_to_public_bucket(data: bytes):
    s3 = S3(environ.get('ACCESS_PATH'), environ.get('PUBLIC_BUCKET'))
    return s3.put(data)

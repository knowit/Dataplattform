from dataplattform.common.aws import S3
from os import environ


def write_to_private_bucket(data: bytes, ext):
    access_path = 'private/'
    s3 = S3(access_path, environ.get('PRIVATE_BUCKET'))
    return s3.put_raw(data, ext=ext)


def write_to_public_bucket(data: bytes, ext: str):
    s3 = S3(environ.get('ACCESS_PATH'), environ.get('PUBLIC_BUCKET'))
    return s3.put_raw(data, ext=ext)

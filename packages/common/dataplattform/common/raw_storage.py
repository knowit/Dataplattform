from dataplattform.common.aws import S3
from os import environ


def write_file_to_bucket(data: bytes, filename: str = ''):
    bucket = environ.get('PUBLIC_BUCKET')

    s3 = S3(access_path='', bucket=bucket)
    return s3.put_raw(data=data, key=filename)

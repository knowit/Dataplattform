from dataplattform.common.aws import S3
from dataplattform.common.aws import path_join
from os import environ


class RawStorage():

    def write_to_private_bucket(self, data: bytes, ext: str, sub_path: str = ''):
        return self._write_to_bucket(data, ext, 'private', sub_path, bucket=environ.get('PRIVATE_BUCKET'))

    def write_to_public_bucket(self, data: bytes, ext: str, sub_path: str = ''):
        return self._write_to_bucket(data, ext, 'public', sub_path, bucket=environ.get('PUBLIC_BUCKET'))

    def _write_to_bucket(self, data: bytes, ext: str, access_path: str = '', sub_path: str = '',
                         bucket: str = environ.get('PRIVATE_BUCKET')):
        access_path = path_join(access_path, sub_path)
        s3 = S3(access_path=access_path, bucket=bucket)
        return s3.put_raw(data, ext=ext)

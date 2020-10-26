from dataplattform.common.aws import S3


class RawStorage():

    def __init__(self):
        self.access_path = ''

    def write_file_to_bucket(self, data: bytes, filename: str = '',
                             bucket: str = None):

        s3 = S3(access_path=self.access_path, bucket=bucket)
        return s3.put_raw(data=data, key=filename)

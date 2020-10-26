from dataplattform.common.raw_storage import RawStorage
from os import environ


def test_s3_private_put_data(s3_private_bucket):
    rs = RawStorage()
    filename = 'private/whatever.txt'
    key = rs.write_file_to_bucket(data='some bytes', filename=filename, bucket=environ.get('PRIVATE_BUCKET'))
    res = s3_private_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'
    assert filename == key


def test_s3_public_put_data(s3_public_bucket):
    rs = RawStorage()
    filename = 'public/whatever.txt'
    key = rs.write_file_to_bucket('some bytes', bucket=environ.get('PUBLIC_BUCKET'), filename=filename)
    res = s3_public_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'
    assert filename == key

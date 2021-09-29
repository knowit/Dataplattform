from dataplattform.common.raw_storage import write_file_to_bucket
from os import environ


def test_s3_private_put_data(s3_private_bucket):
    filename = 'private/whatever.txt'
    key = write_file_to_bucket(data='some bytes', filename=filename, bucket=environ.get('PRIVATE_BUCKET'))
    res = s3_private_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'
    assert filename == key


def test_s3_public_put_data(s3_public_bucket):
    filename = 'public/whatever.txt'
    key = write_file_to_bucket('some bytes', bucket=environ.get('PUBLIC_BUCKET'), filename=filename)
    res = s3_public_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'
    assert filename == key


def test_s3_put_data_fallback(s3_public_bucket, s3_private_bucket):
    filename = 'whatever.txt'
    key = write_file_to_bucket('some bytes', bucket='invalid_bucket', filename=filename)
    res = s3_private_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'
    assert filename == key
    assert list(s3_public_bucket.objects.all()) == []

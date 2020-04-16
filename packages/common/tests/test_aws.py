from dataplattform.common import aws, schema
from os import environ
from pytest import mark


def test_s3_default():
    s3 = aws.S3()
    assert s3.access_path == environ.get("ACCESS_PATH") and\
        s3.bucket == environ.get('DATALAKE')


def test_s3_default_overrides():
    s3 = aws.S3(access_path='/abc', bucket='myBucket')
    assert s3.access_path == '/abc' and\
        s3.bucket == 'myBucket'


@mark.parametrize('path, expected_key', [
    ('', 'abc/123/1234.json'),
    ('test', 'abc/123/test/1234.json'),
    ('test/', 'abc/123/test/1234.json')
])
def test_s3_key(path, expected_key):
    s3 = aws.S3(access_path='abc/123')
    key = s3.put(
        schema.Data(
            metadata=schema.Metadata(timestamp=1234),
            data=''),
        path=path)
    assert key == expected_key


def test_s3_put_data(s3_bucket):
    s3 = aws.S3()
    key = s3.put(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='test'))

    res = schema.Data.from_json(s3_bucket.Object(key).get()['Body'].read())
    assert res.data == 'test'


def test_ssm_default():
    ssm = aws.SSM()
    assert ssm.path.startswith('/') and\
        environ.get('STAGE') in ssm.path and\
        ssm.path.endswith(environ.get('SERVICE'))


def test_ssm_get_paramenter(ssm_client):
    ssm_client.put_parameter(
        Name='/test/param',
        Value='hello world',
        Type='String',
        Tier='Standard')

    ssm = aws.SSM(path='/test')
    assert ssm.get('param') == 'hello world'


def test_s3_get_data(s3_bucket):
    s3_bucket.Object('/data/test.txt').put(Body='test'.encode('utf-8'))

    s3 = aws.S3(access_path='/data')
    test_text = s3.get('test.txt').raw
    assert b'test' == test_text


def test_s3_get_empty():
    s3 = aws.S3(access_path='/data')
    res = s3.get('test.txt')
    assert res.raw is None and \
        'NoSuchKey' in str(res.error)


def test_s3_get_absolute_path_data(s3_bucket):
    s3_bucket.Object('/data/test.txt').put(Body='test'.encode('utf-8'))

    s3 = aws.S3(access_path='/data')
    test_text = s3.get('/data/test.txt').raw
    assert b'test' == test_text


def test_s3_get_data_json(s3_bucket):
    s3_bucket.Object('/data/test.json').put(Body='{"hello":"world"}'.encode('utf-8'))

    s3 = aws.S3(access_path='/data')
    test_json = s3.get('test.json').json()
    assert test_json['hello'] == 'world'

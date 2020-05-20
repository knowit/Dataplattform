from dataplattform.common import aws, schema
from dataplattform.testing.util import ignore_policy
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
def test_s3_key(path, expected_key, iam_user):
    iam_user.use_policy('s3:PutObject')

    s3 = aws.S3(access_path='abc/123')
    key = s3.put(
        schema.Data(
            metadata=schema.Metadata(timestamp=1234),
            data=''),
        path=path)
    assert key == expected_key


def test_s3_put_data(s3_bucket, iam_user):
    iam_user.use_policy('s3:PutObject')

    s3 = aws.S3()
    key = s3.put(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='test'))

    with ignore_policy():
        res = schema.Data.from_json(s3_bucket.Object(key).get()['Body'].read())
    assert res.data == 'test'


def test_ssm_default():
    ssm = aws.SSM()
    assert ssm.path.startswith('/') and\
        environ.get('STAGE') in ssm.path and\
        ssm.path.endswith(environ.get('SERVICE'))


def test_ssm_get_paramenter(ssm_client, iam_user):
    iam_user.use_policy('ssm:GetParameter')
    with ignore_policy():
        ssm_client.put_parameter(
            Name='/test/param',
            Value='hello world',
            Type='String',
            Tier='Standard')

    ssm = aws.SSM(path='/test')
    assert ssm.get('param') == 'hello world'


def test_ssm_get_list_1_paramenter(ssm_client, iam_user):
    iam_user.use_policy('ssm:GetParameter')
    with ignore_policy():
        ssm_client.put_parameter(
            Name='/test/param',
            Value='hello world',
            Type='StringList',
            Tier='Standard')

    ssm = aws.SSM(path='/test')
    assert ssm.get('param') == ['hello world']


def test_ssm_get_list_2_paramenter(ssm_client, iam_user):
    iam_user.use_policy('ssm:GetParameter')
    with ignore_policy():
        ssm_client.put_parameter(
            Name='/test/param',
            Value='hello,world',
            Type='StringList',
            Tier='Standard')

    ssm = aws.SSM(path='/test')
    assert ssm.get('param') == ['hello', 'world']


def test_s3_get_data(s3_bucket, iam_user):
    iam_user.use_policy('s3:GetObject')
    with ignore_policy():
        s3_bucket.Object('/data/test.txt').put(Body='test'.encode('utf-8'))

    s3 = aws.S3(access_path='/data')
    test_text = s3.get('test.txt').raw
    assert b'test' == test_text


def test_s3_get_empty(iam_user):
    iam_user.use_policy('s3:GetObject')
    s3 = aws.S3(access_path='/data')
    res = s3.get('test.txt')
    assert res.raw is None and \
        'NoSuchKey' in str(res.error)


def test_s3_get_absolute_path_data(s3_bucket, iam_user):
    iam_user.use_policy('s3:GetObject')
    with ignore_policy():
        s3_bucket.Object('/data/test.txt').put(Body='test'.encode('utf-8'))

    s3 = aws.S3(access_path='/data')
    test_text = s3.get('/data/test.txt').raw
    assert b'test' == test_text


def test_s3_get_data_json(s3_bucket, iam_user):
    iam_user.use_policy('s3:GetObject')
    with ignore_policy():
        s3_bucket.Object('/data/test.json').put(Body='{"hello":"world"}'.encode('utf-8'))

    s3 = aws.S3(access_path='/data')
    test_json = s3.get('test.json').json()
    assert test_json['hello'] == 'world'


def test_s3fs_open_write(s3_bucket, iam_user):
    iam_user.use_policy('s3:PutObject')
    s3 = aws.S3(access_path='data')

    with s3.fs.open('test.txt', 'w') as f:
        f.write('test')

    with ignore_policy():
        assert s3_bucket.Object('data/test.txt').get()['Body'].read() == b'test'


def test_s3fs_open_read(s3_bucket, iam_user):
    iam_user.use_policy('s3:GetObject')

    with ignore_policy():
        s3_bucket.Object('/data/test.txt').put(Body='test'.encode('utf-8'))

    s3 = aws.S3(access_path='data')
    with s3.fs.open('test.txt', 'r') as f:
        assert f.read() == 'test'


def test_s3fs_exists(s3_bucket, iam_user):
    iam_user.use_policy('s3:GetObject')

    with ignore_policy():
        s3_bucket.Object('/data/test.txt').put(Body='test'.encode('utf-8'))

    s3 = aws.S3(access_path='data')
    assert s3.fs.exists('test.txt') is True

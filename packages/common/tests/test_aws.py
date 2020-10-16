from dataplattform.common import aws, schema
from os import environ
from pytest import mark
import re

uuid_regex = r'[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}'


def test_s3_default():
    s3 = aws.S3()
    assert s3.access_path == environ.get("ACCESS_PATH") and\
        s3.bucket == environ.get('DATALAKE')


def test_s3_default_overrides():
    s3 = aws.S3(access_path='/abc', bucket='myBucket')
    assert s3.access_path == '/abc' and\
        s3.bucket == 'myBucket'


@mark.parametrize('path, expected_key_pattern', [
    ('', f'abc/123/{uuid_regex}.json'),
    ('test', f'abc/123/test/{uuid_regex}.json'),
    ('test/', f'abc/123/test/{uuid_regex}.json')
])
def test_s3_key(path, expected_key_pattern):
    s3 = aws.S3(access_path='abc/123')
    key = s3.put(
        schema.Data(
            metadata=schema.Metadata(timestamp=1234),
            data=''),
        path=path)

    assert re.fullmatch(expected_key_pattern, key)


def test_s3_put_data(s3_bucket):
    s3 = aws.S3()
    key = s3.put(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='test'))

    res = schema.Data.from_json(s3_bucket.Object(key).get()['Body'].read())
    assert res.data == 'test'


def test_s3_put_raw_data(s3_bucket):
    s3 = aws.S3()
    input_bytes = 'some bytes'
    ext = '.txt'
    key = s3.put_raw(input_bytes, path='', ext=ext)
    res = s3_bucket.Object(key).get()['Body'].read().decode('utf-8')

    assert res == input_bytes
    assert ext in key


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


def test_ssm_get_list_1_paramenter(ssm_client):
    ssm_client.put_parameter(
        Name='/test/param',
        Value='hello world',
        Type='StringList',
        Tier='Standard')

    ssm = aws.SSM(path='/test')
    assert ssm.get('param') == ['hello world']


def test_ssm_get_list_2_paramenter(ssm_client):
    ssm_client.put_parameter(
        Name='/test/param',
        Value='hello,world',
        Type='StringList',
        Tier='Standard')

    ssm = aws.SSM(path='/test')
    assert ssm.get('param') == ['hello', 'world']


def test_SSM_put():
    ssm = aws.SSM()
    ssm.put(name='/test/param',
            value='hello world')
    ssm = aws.SSM(path='/test')
    assert ssm.get('param') == 'hello world'


def test_SSM_put_overwrite_true():
    ssm = aws.SSM()
    ssm.put(name='/test/param',
            value='hello world')
    ssm = aws.SSM(path='/test')
    assert ssm.get('param') == 'hello world'
    ssm.put(name='param',
            value='hello new world',
            overwrite=True)
    assert ssm.get('param') == 'hello new world'


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


def test_s3fs_open_write(s3_bucket):
    s3 = aws.S3(access_path='data')

    with s3.fs.open('test.txt', 'w') as f:
        f.write('test')

    assert s3_bucket.Object('data/test.txt').get()['Body'].read() == b'test'


def test_s3fs_open_read(s3_bucket):
    s3_bucket.Object('/data/test.txt').put(Body='test'.encode('utf-8'))

    s3 = aws.S3(access_path='data')
    with s3.fs.open('test.txt', 'r') as f:
        assert f.read() == 'test'


def test_s3fs_exists(s3_bucket):
    s3_bucket.Object('/data/test.txt').put(Body='test'.encode('utf-8'))

    s3 = aws.S3(access_path='data')
    assert s3.fs.exists('test.txt') is True


def test_sqs_send_message(sqs_queue):
    sqs = aws.SQS()
    msg_id = sqs.send_custom_filename_message('file_name')

    message = next(iter(sqs_queue.receive_messages()))
    assert msg_id == message.message_id


def test_sqs_send_message_body(sqs_queue):
    sqs = aws.SQS()
    sqs.send_custom_filename_message('file_name')

    message = next(iter(sqs_queue.receive_messages()))
    assert message.body == 'file_name'


def test_sqs_send_message_attributes(sqs_queue):
    sqs = aws.SQS()
    sqs.send_custom_filename_message('file_name')

    message = next(iter(sqs_queue.receive_messages()))
    assert message.message_attributes['s3FileName']['StringValue'] == 'file_name'

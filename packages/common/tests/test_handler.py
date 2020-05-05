from dataplattform.common import handler, schema
import pandas as pd
import re


def test_empty_handler():
    ingest_handler = handler.Handler()
    res = ingest_handler(None)

    assert res['statusCode'] == 200 and res['body'] == ''


def test_handler_response():
    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test(event):
        return handler.Response(body='hello test')

    res = ingest_handler(None)
    assert res['body'] == 'hello test'


def test_handler_data(s3_bucket):
    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test(event):
        return schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='hello test'
        )

    ingest_handler(None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = schema.Data.from_json(response['Body'].read())
    assert data.data == 'hello test'


def test_handler_validate(mocker):
    ingest_handler = handler.Handler()

    @ingest_handler.validate()
    def test_validate(event):
        return False

    res = ingest_handler(None)
    assert res['statusCode'] == 403


def test_handler_invalid_skip_ingest(mocker):
    ingest_handler = handler.Handler()

    @ingest_handler.validate()
    def test_validate(event):
        return False

    ingest_handler.wrapped_func['ingest'] = mocker.stub()

    ingest_handler(None)

    ingest_handler.wrapped_func['ingest'].assert_not_called()


def test_handler_valid_call_ingest(mocker):
    ingest_handler = handler.Handler()

    @ingest_handler.validate()
    def test_validate(event):
        return True

    ingest_handler.wrapped_func['ingest'] = mocker.MagicMock(return_value=handler.Response())

    ingest_handler(None)

    ingest_handler.wrapped_func['ingest'].assert_called_once()


def test_handler_call_process(mocker):
    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='hello test'
        )

    ingest_handler.wrapped_func['process'] = mocker.MagicMock(return_value={})
    ingest_handler(None)

    ingest_handler.wrapped_func['process'].assert_called_once()
    assert ingest_handler.wrapped_func['process'].call_args[0][0][0].json()['data'] == 'hello test'


def test_handler_call_process_with_s3_data(s3_bucket, mocker):
    s3_bucket.Object('/data/test.json').put(
            Body=schema.Data(
                metadata=schema.Metadata(timestamp=0),
                data='hello test'
            ).to_json().encode('utf-8'))

    ingest_handler = handler.Handler()

    ingest_handler.wrapped_func['process'] = mocker.MagicMock(return_value={})
    ingest_handler({
        'Records': [{
            's3': {
                'object': {'key': '/data/test.json'}
            }
        }]
    })

    ingest_handler.wrapped_func['process'].assert_called_once()
    assert ingest_handler.wrapped_func['process'].call_args[0][0][0].json()['data'] == 'hello test'


def test_handler_call_process_to_parquet(mocker):
    df_mock = mocker.MagicMock()
    df_mock.to_parquet = mocker.stub()

    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(data='hello test')

    @ingest_handler.process(partitions={})
    def test_process(data):
        return {
            'test': df_mock
        }

    ingest_handler(None)

    df_mock.to_parquet.assert_called_once()
    assert df_mock.to_parquet.call_args[0][0] == 'structured/test'


def test_handler_call_process_s3_parquet(s3_bucket):
    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(data='')

    @ingest_handler.process(partitions={})
    def test_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 1], 'b': [1, 2, 3]})
        }

    ingest_handler(None)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]

    assert all([re.fullmatch(r'data\/test\/structured\/test\/\w{32}\.parquet', key) for key in keys_in_s3]) \
        and len(keys_in_s3) == 1


def test_handler_call_process_s3_parquet_append(s3_bucket):
    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(data='')

    @ingest_handler.process(partitions={})
    def test_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 1], 'b': [1, 2, 3]})
        }

    ingest_handler(None)
    ingest_handler(None)  # Called twice

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]

    assert all([re.fullmatch(r'data\/test\/structured\/test\/\w{32}\.parquet', key) for key in keys_in_s3]) \
        and len(keys_in_s3) == 2


def test_handler_call_process_s3_parquet_partitioned(s3_bucket):
    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(data='')

    @ingest_handler.process(partitions={'test': ['a']})
    def test_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [1, 2, 3]})
        }

    ingest_handler(None)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    assert all([re.fullmatch(r'data\/test\/structured\/test\/a=[1,2]\/\w{32}\.parquet', key) for key in keys_in_s3]) \
        and len(keys_in_s3) == 2


def test_handler_call_process_s3_parquet_schema_upgrade(s3_bucket):
    old_ingest_handler = handler.Handler()
    new_ingest_handler = handler.Handler()

    @old_ingest_handler.ingest()
    @new_ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(data='')

    @old_ingest_handler.process(partitions={})
    def test_old_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [1, 2, 3]})
        }

    @new_ingest_handler.process(partitions={})
    def test_new_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': ['1', '2', '3']})
        }

    old_ingest_handler(None)
    new_ingest_handler(None)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]

    print(keys_in_s3)
    assert False

from dataplattform.common import handler, schema
from dataplattform.testing.util import ignore_policy
import pandas as pd
import re
import pytest


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


def test_handler_data(s3_bucket, iam_user):
    iam_user.use_policy('s3:PutObject')
    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test(event):
        return schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='hello test'
        )

    ingest_handler(None)

    with ignore_policy():
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


def test_handler_call_process(mocker, iam_user):
    iam_user.use_policy('s3:PutObject')

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


def test_handler_call_process_with_s3_data(s3_bucket, mocker, iam_user):
    iam_user.use_policy('s3:PutObject', 's3:GetObject')

    with ignore_policy():
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


def test_handler_call_process_to_parquet(mocker, iam_user):
    iam_user.use_policy('s3:PutObject')

    df_mock = mocker.MagicMock()
    df_mock.to_parquet = mocker.stub()
    df_mock.empty = False

    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='hello test'
        )

    @ingest_handler.process(partitions={})
    def test_process(data):
        return {
            'test': df_mock
        }

    ingest_handler(None)

    df_mock.to_parquet.assert_called_once()
    assert df_mock.to_parquet.call_args[0][0] == 'structured/test'


def test_handler_call_process_skip_empty_dataframe_to_parquet(mocker, iam_user):
    iam_user.use_policy('s3:PutObject')

    ingest_handler = handler.Handler()

    empty_df = pd.DataFrame()
    to_parquet_spy = mocker.spy(empty_df, 'to_parquet')

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='hello test'
        )

    @ingest_handler.process(partitions={})
    def test_process(data):
        return {
            'test': empty_df
        }

    ingest_handler(None)

    to_parquet_spy.assert_not_called()


def test_handler_call_process_s3_parquet(s3_bucket, iam_user):
    iam_user.use_policy('s3:PutObject')

    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(metadata=schema.Metadata(timestamp=0), data='')

    @ingest_handler.process(partitions={})
    def test_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 1], 'b': [1, 2, 3]})
        }

    ingest_handler(None)

    with ignore_policy():
        keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/part.0.parquet',
    ]

    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])


def test_handler_call_process_s3_parquet_append(s3_bucket, iam_user):
    iam_user.use_policy('s3:PutObject', 's3:GetObject', 's3:ListObjects', 's3:ListObjectsV2')

    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(metadata=schema.Metadata(timestamp=0), data='')

    @ingest_handler.process(partitions={})
    def test_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 1], 'b': [1, 2, 3]})
        }

    ingest_handler(None)
    ingest_handler(None)  # Called twice

    with ignore_policy():
        keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/part.0.parquet',
        'data/test/structured/test/part.1.parquet',
    ]

    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])


def test_handler_call_process_s3_parquet_partitioned(s3_bucket, iam_user):
    iam_user.use_policy('s3:PutObject', 's3:ListObjectsV2')

    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(metadata=schema.Metadata(timestamp=0), data='')

    @ingest_handler.process(partitions={'test': ['a']})
    def test_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [1, 2, 3]})
        }

    ingest_handler(None)
    with ignore_policy():
        keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/a=1/part.0.parquet',
        'data/test/structured/test/a=2/part.0.parquet'
    ]

    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])


def test_handler_call_process_s3_parquet_append_partitioned(s3_bucket, iam_user):
    iam_user.use_policy('s3:PutObject')

    ingest_handler = handler.Handler()

    @ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(metadata=schema.Metadata(timestamp=0), data='')

    @ingest_handler.process(partitions={'test': ['a']})
    def test_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [1, 2, 3]})
        }

    ingest_handler(None)
    ingest_handler(None)  # Called twice

    with ignore_policy():
        keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/a=1/part.0.parquet',
        'data/test/structured/test/a=1/part.1.parquet',
        'data/test/structured/test/a=2/part.0.parquet',
        'data/test/structured/test/a=2/part.1.parquet',
    ]

    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])


def test_handler_call_process_s3_parquet_schema_upgrade(s3_bucket, iam_user):
    iam_user.use_policy('s3:PutObject')

    old_ingest_handler = handler.Handler()
    new_ingest_handler = handler.Handler()

    @old_ingest_handler.ingest()
    @new_ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(metadata=schema.Metadata(timestamp=0), data='')

    @old_ingest_handler.process(partitions={})
    def test_old_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [1, 2, 3]})
        }

    @new_ingest_handler.process(partitions={})
    def test_new_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': ['1', '2', '3']})  # New datatype
        }

    old_ingest_handler(None)
    new_ingest_handler(None)

    with ignore_policy():
        dep_keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured/deprecated' in x.key]
        new_keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key and 'deprecated' not in x.key]

    expected_dep_keys = [
        r'data\/test\/structured\/deprecated\/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\/test\/_common_metadata',
        r'data\/test\/structured\/deprecated\/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\/test\/_metadata',
        r'data\/test\/structured\/deprecated\/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\/test\/part.0.parquet']
    expected_new_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/part.0.parquet']

    assert all([new_keys_in_s3[i] == expected_new_keys[i] for i in range(len(new_keys_in_s3))]) \
        and all([re.fullmatch(expected_dep_keys[i], dep_keys_in_s3[i]) for i in range(len(dep_keys_in_s3))])


@pytest.mark.parametrize(
    'old_partitions,new_partitions,expected_dep_keys,expected_new_keys',
    [
        (
            ['a', 'b'],
            ['b'],
            ['a=1/b=2/part.0.parquet', 'a=2/b=3/part.0.parquet'],
            ['b=2/part.0.parquet', 'b=3/part.0.parquet']
        ),
        (
            ['a'],
            [],
            ['a=1/part.0.parquet', 'a=2/part.0.parquet'],
            ['part.0.parquet']
        ),
        (
            ['a'],
            ['b'],
            ['a=1/part.0.parquet', 'a=2/part.0.parquet'],
            ['b=2/part.0.parquet', 'b=3/part.0.parquet']
        ),
        (
            [],
            ['b'],
            ['part.0.parquet'],
            ['b=2/part.0.parquet', 'b=3/part.0.parquet']
        ),
        (
            ['a'],
            ['a', 'b'],
            ['a=1/part.0.parquet', 'a=2/part.0.parquet'],
            ['a=1/b=2/part.0.parquet', 'a=2/b=3/part.0.parquet']
        )
    ])
def test_handler_call_process_s3_parquet_schema_partition_change(s3_bucket,
                                                                 iam_user,
                                                                 old_partitions,
                                                                 new_partitions,
                                                                 expected_dep_keys,
                                                                 expected_new_keys):
    iam_user.use_policy('s3:PutObject')

    old_ingest_handler = handler.Handler()
    new_ingest_handler = handler.Handler()

    @old_ingest_handler.ingest()
    @new_ingest_handler.ingest()
    def test_ingest(event):
        return schema.Data(metadata=schema.Metadata(timestamp=0), data='')

    @old_ingest_handler.process(partitions={'test': old_partitions})
    def test_old_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [2, 2, 3], 'c': [1, 2, 3]})
        }

    @new_ingest_handler.process(partitions={'test': new_partitions})
    def test_new_process(data):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [2, 2, 3], 'c': [1, 2, 3]})
        }

    old_ingest_handler(None)
    new_ingest_handler(None)

    with ignore_policy():
        dep_keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured/deprecated' in x.key]
        new_keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key and 'deprecated' not in x.key]

    expected_dep_keys = [
        'data\\/test\\/structured\\/deprecated\\/\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\/test\\/' + x
        for x in ['_common_metadata', '_metadata'] + [s.replace('/', '\\/') for s in expected_dep_keys]
    ]

    expected_new_keys = [
        f'data/test/structured/test/{x}'
        for x in ['_common_metadata', '_metadata'] + expected_new_keys
    ]

    assert all([new_keys_in_s3[i] == expected_new_keys[i] for i in range(len(new_keys_in_s3))]) \
        and all([re.fullmatch(expected_dep_keys[i], dep_keys_in_s3[i]) for i in range(len(dep_keys_in_s3))])

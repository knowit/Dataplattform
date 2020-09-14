from dataplattform.common import schema
from dataplattform.common.handlers import process as handler
import re
import pytest
import pandas as pd
from pytest import fixture


@fixture
def setup_queue_event(s3_bucket):
    def make_queue_event(data: schema.Data):
        s3_bucket.Object('/data/test.json').put(
            Body=data.to_json().encode('utf-8'))
        return {
            'Records': [{
                'body': '/data/test.json',
                'messageAttributes': {
                    's3FileName': {
                        'stringValue': '/data/test.json'
                    }
                }
            }]
        }
    yield make_queue_event


def test_handler_call_process(mocker, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='hello test'))

    ingest_handler = handler.ProcessHandler()

    ingest_handler.wrapped_func['process'] = mocker.MagicMock(return_value={})
    ingest_handler(event)

    ingest_handler.wrapped_func['process'].assert_called_once()
    assert ingest_handler.wrapped_func['process'].call_args[0][0][0].json()['data'] == 'hello test'


def test_handler_call_process_to_parquet(mocker, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))

    df_mock = mocker.MagicMock()
    df_mock.__class__ = pd.DataFrame
    df_mock.to_parquet = mocker.stub()
    df_mock.empty = False

    ingest_handler = handler.ProcessHandler()

    @ingest_handler.process(partitions={})
    def test_process(data, events):
        return {
            'test': df_mock
        }

    ingest_handler(event)

    df_mock.to_parquet.assert_called_once()
    assert df_mock.to_parquet.call_args[0][0] == 'structured/test'


def test_handler_call_process_skip_empty_dataframe_to_parquet(mocker, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))

    ingest_handler = handler.ProcessHandler()

    empty_df = pd.DataFrame()
    to_parquet_spy = mocker.spy(empty_df, 'to_parquet')

    @ingest_handler.process(partitions={})
    def test_process(data, events):
        return {
            'test': empty_df
        }

    ingest_handler(event)

    to_parquet_spy.assert_not_called()


def test_handler_call_process_s3_parquet(s3_bucket, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))

    ingest_handler = handler.ProcessHandler()

    @ingest_handler.process(partitions={})
    def test_process(data, events):
        return {
            'test': pd.DataFrame({'a': [1, 1, 1], 'b': [1, 2, 3]})
        }

    ingest_handler(event)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/part.0.parquet',
    ]

    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])


def test_handler_call_process_s3_parquet_append(s3_bucket, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))
    ingest_handler = handler.ProcessHandler()

    @ingest_handler.process(partitions={})
    def test_process(data, events):
        return {
            'test': pd.DataFrame({'a': [1, 1, 1], 'b': [1, 2, 3]})
        }

    ingest_handler(event)
    ingest_handler(event)  # Called twice

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/part.0.parquet',
        'data/test/structured/test/part.1.parquet',
    ]

    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])


def test_handler_call_process_s3_parquet_overwrite(s3_bucket, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))

    process_handler = handler.ProcessHandler()

    def decorate_process_function(count):
        if (count == 0):
            @process_handler.process(partitions={'test': ['a']})
            def test_process(data, events):
                return {
                   'test': pd.DataFrame({'a': [1, 1, 1], 'c': [1, 2, 3]})
                }
        else:
            @process_handler.process(partitions={'test': ['a']}, overwrite=True)
            def test_process(data, events):
                return {
                    'test': pd.DataFrame({'a': [2, 2, 2], 'c': [1, 2, 3]})
                }

    decorate_process_function(0)
    process_handler(event)
    keys_in_s3_first_time = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/a=1/part.0.parquet',
    ]

    assert all([keys_in_s3_first_time[i] == expected_keys[i] for i in range(len(keys_in_s3_first_time))])

    decorate_process_function(1)
    process_handler(event)

    keys_in_s3_second_time = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    print(keys_in_s3_second_time)
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/a=2/part.0.parquet',
    ]

    assert all([keys_in_s3_second_time[i] == expected_keys[i] for i in range(len(keys_in_s3_second_time))])


def test_handler_call_process_s3_parquet_partitioned(s3_bucket, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))
    ingest_handler = handler.ProcessHandler()

    @ingest_handler.process(partitions={'test': ['a']})
    def test_process(data, events):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [1, 2, 3]})
        }

    ingest_handler(event)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/a=1/part.0.parquet',
        'data/test/structured/test/a=2/part.0.parquet'
    ]

    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])


def test_handler_call_process_s3_parquet_partitioned_with_None_content(s3_bucket, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))
    ingest_handler = handler.ProcessHandler()

    @ingest_handler.process(partitions={'test': ['a']})
    def test_process(data, events):
        return {
            'test': pd.DataFrame({'a': [1, 2, None], 'b': [1, 2, 3]})
        }

    ingest_handler(event)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]

    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/a=-1.0/part.0.parquet',
        'data/test/structured/test/a=1.0/part.0.parquet',
        'data/test/structured/test/a=2.0/part.0.parquet'
    ]

    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])


def test_handler_call_process_s3_parquet_partitioned_with_None_content_string(s3_bucket, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))
    ingest_handler = handler.ProcessHandler()

    @ingest_handler.process(partitions={'test': ['a']})
    def test_process(data, events):
        return {
            'test': pd.DataFrame({'a': ['name0', 'name0', None], 'b': [1, 2, 3]})
        }

    ingest_handler(event)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/test/_common_metadata',
        'data/test/structured/test/_metadata',
        'data/test/structured/test/a=name0/part.0.parquet',
        'data/test/structured/test/a=undefined/part.0.parquet'
    ]

    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])


def test_handler_call_process_s3_parquet_append_partitioned(s3_bucket, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))
    ingest_handler = handler.ProcessHandler()

    @ingest_handler.process(partitions={'test': ['a']})
    def test_process(data, events):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [1, 2, 3]})
        }

    ingest_handler(event)
    ingest_handler(event)  # Called twice

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


def test_handler_call_process_s3_parquet_schema_upgrade(s3_bucket, setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))
    old_ingest_handler = handler.ProcessHandler()
    new_ingest_handler = handler.ProcessHandler()

    @old_ingest_handler.process(partitions={})
    def test_old_process(data, events):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [1, 2, 3]})
        }

    @new_ingest_handler.process(partitions={})
    def test_new_process(data, events):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': ['1', '2', '3']})  # New datatype
        }

    old_ingest_handler(event)
    new_ingest_handler(event)

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
                                                                 old_partitions,
                                                                 new_partitions,
                                                                 expected_dep_keys,
                                                                 expected_new_keys,
                                                                 setup_queue_event):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=''))
    old_ingest_handler = handler.ProcessHandler()
    new_ingest_handler = handler.ProcessHandler()

    @old_ingest_handler.process(partitions={'test': old_partitions})
    def test_old_process(data, events):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [2, 2, 3], 'c': [1, 2, 3]})
        }

    @new_ingest_handler.process(partitions={'test': new_partitions})
    def test_new_process(data, events):
        return {
            'test': pd.DataFrame({'a': [1, 1, 2], 'b': [2, 2, 3], 'c': [1, 2, 3]})
        }

    old_ingest_handler(event)
    new_ingest_handler(event)

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

from googlesheets.google_sheets_webhook_process_lambda import handler as process_handler
from dataplattform.common import schema
from json import load
from os import path
from pytest import fixture
import pandas as pd


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


@fixture
def test_data1():
    with open(path.join(path.dirname(__file__), 'test_data1.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data2():
    with open(path.join(path.dirname(__file__), 'test_data2.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data3():
    with open(path.join(path.dirname(__file__), 'test_data3.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data4():
    with open(path.join(path.dirname(__file__), 'test_data4.json'), 'r') as json_file:
        yield load(json_file)


def test_insert_data_process(setup_queue_event, test_data1, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data1))

    process_handler(event, None)

    create_table_mock.assert_table_data_column(
        'test_test_b_enkel_test_ark_1',
        'a',
        pd.Series([1, 5, 1]))

    create_table_mock.assert_table_data_column(
        'test_test_b_enkel_test_ark_1',
        'b',
        pd.Series([4, 8, 4]))

    create_table_mock.assert_table_data_column(
        'test_test_b_enkel_test_ark_1',
        'c',
        pd.Series([5, 13, 5]))


def test_process_clean_data(setup_queue_event, test_data2, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data2))

    process_handler(event, None)

    create_table_mock.assert_table_data_column(
        'test2_test_b_enkel_test_ark_2',
        'a',
        pd.Series([1, 5, 1]))

    create_table_mock.assert_table_data_column(
        'test2_test_b_enkel_test_ark_2',
        'b',
        pd.Series([4, 8, 4]))

    create_table_mock.assert_table_data_column(
        'test2_test_b_enkel_test_ark_2',
        'c',
        pd.Series([5, 13, 5]))


def test_process_mixed_data(setup_queue_event, test_data3, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data3))

    process_handler(event, None)

    create_table_mock.assert_table_data_column(
        'test_test_b_enkel_test_ark_3',
        'c',
        pd.Series([5, 'a', 5]))


def test_process_missing_data(setup_queue_event, test_data4, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data4))

    process_handler(event, None)

    create_table_mock.assert_table_data_column(
        'test_test_b_enkel_test_ark_4',
        'c',
        pd.Series([5, pd.NA, 5]))


def test_process_parquet_get_data(setup_queue_event, create_table_mock, test_data1):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data1))

    process_handler(event, None)

    create_table_mock.assert_table_data_column(
        'google_sheets_metadata',
        'uploaded_by_user',
        pd.Series(['test@test.b']))


def test_process_parquet_add_twice(setup_queue_event, create_table_mock, test_data1, test_data2):
    event1 = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data1))

    process_handler(event1, None)

    event2 = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data2))

    process_handler(event2, None)

    create_table_mock.assert_table_data_column(
        'google_sheets_metadata',
        'uploaded_by_user',
        pd.Series(['test@test.b', 'test2@test.b']))

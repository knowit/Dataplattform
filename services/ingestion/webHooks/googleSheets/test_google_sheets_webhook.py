from google_sheets_webhook import handler
from dataplattform.testing.events import APIGateway
from json import loads, load
from os import path
from pytest import fixture
import pandas as pd


@fixture
def test_data1():
    with open(path.join(path.dirname(__file__), 'test_data1.json'), 'r') as json_file:
        yield json_file.read()


@fixture
def test_data2():
    with open(path.join(path.dirname(__file__), 'test_data2.json'), 'r') as json_file:
        yield json_file.read()


@fixture
def test_data3():
    with open(path.join(path.dirname(__file__), 'test_data3.json'), 'r') as json_file:
        yield json_file.read()


@fixture
def test_data4():
    with open(path.join(path.dirname(__file__), 'test_data4.json'), 'r') as json_file:
        yield json_file.read()


def test_insert_data(s3_bucket, test_data1, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data1).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data']['tableName'] == 'enkel_test_ark 1'

    create_table_mock.assert_table_data_column(
        'enkel_test_ark 1',
        'a',
        pd.Series([1, 5, 1]))

    create_table_mock.assert_table_data_column(
        'enkel_test_ark 1',
        'b',
        pd.Series([4, 8, 4]))

    create_table_mock.assert_table_data_column(
        'enkel_test_ark 1',
        'c',
        pd.Series([5, 13, 5]))


def test_process_clean_data(s3_bucket, test_data2, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data2).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data']['tableName'] == 'enkel_test_ark 2'

    create_table_mock.assert_table_data_column(
        'enkel_test_ark 2',
        'a',
        pd.Series([1, 5, 1]))

    create_table_mock.assert_table_data_column(
        'enkel_test_ark 2',
        'b',
        pd.Series([4, 8, 4]))

    create_table_mock.assert_table_data_column(
        'enkel_test_ark 2',
        'c',
        pd.Series([5, 13, 5]))


def test_process_mixed_data(s3_bucket, test_data3, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data3).to_dict(), None)

    create_table_mock.assert_table_data_column(
        'enkel_test_ark 3',
        'c',
        pd.Series([5, 'a', 5]))


def test_process_missing_data(s3_bucket, test_data4, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data4).to_dict(), None)

    create_table_mock.assert_table_data_column(
        'enkel_test_ark 4',
        'c',
        pd.Series([5, '', 5]))


def test_process_parquet_get_data(mocker, create_table_mock, test_data1):
    handler(APIGateway(
        headers={},
        body=test_data1).to_dict(), None)

    create_table_mock.assert_table_data_column(
        'google_sheets_metadata',
        'author',
        pd.Series(['test@test.b']))

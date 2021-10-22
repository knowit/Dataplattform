import os
from pathlib import PurePosixPath
from pytest import fixture
from ubw_customer_per_resource_process_lambda import handler
import pandas as pd
import numpy as np
import fastparquet as fp
import s3fs
from os import path
import numpy as np
from json import load
from dataplattform.common import schema
from datetime import datetime
from dataplattform.common.aws import S3


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data_old():
    with open(path.join(path.dirname(__file__), 'test_old_data.json'), 'r') as json_file:
        json = load(json_file)
        cur_year, cur_week = datetime.now().isocalendar()[0:2]
        for i in range(len(json['data'])):  # Update reg_period to simulate recent data
            json['data'][i]['reg_period'] = str(cur_year) + str(cur_week - i)
        yield json


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


def test_process_data_reg_period_1(create_table_mock, setup_queue_event, test_data, test_data_old, dynamodb_resource, s3_bucket):
    os.environ['NUM_WEEKS'] = '4'

    event_old_data = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_old['data']))

    handler(event_old_data, None)

    df = create_table_mock.df_from_calls('structured/ubw_customer_per_resource')
    s3_path = PurePosixPath(os.environ.get('DATALAKE'),
                            os.environ.get('ACCESS_PATH'),
                            'structured/ubw_customer_per_resource')
    fp.write(str(s3_path), df, file_scheme='hive', open_with=s3fs.S3FileSystem().open)

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['reg_period_1']))

    handler(event, None)

    cur_year, cur_week = datetime.now().isocalendar()[0:2]
    new_data = pd.Series(['202053',
                          '202053',
                          '202053',
                          str(cur_year) + str(cur_week - 1),
                          str(cur_year) + str(cur_week),
                          str(cur_year) + str(cur_week - 2),
                          str(cur_year) + str(cur_week - 3)])

    # Merge frames here since mocked data table does not overwrite old data
    data = pd.concat([df['reg_period'], new_data]).reset_index()

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'reg_period',
        data[0])


def test_process_data_reg_period_2(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['reg_period_2']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'reg_period',
        pd.Series(['202140', '202140']))


def test_process_data_test_weigth_reg_period_1(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['reg_period_1']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'weigth',
        pd.Series([1, 2, 1]))

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'customer',
        pd.Series(['customer 2', 'customer 1', 'customer 3']))


def test_process_data_test_weigth_reg_period_2(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['reg_period_2']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'weigth',
        pd.Series([1, 1]))

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'customer',
        pd.Series(['Entur AS', 'Entur AS']))


def test_process_data_test_used_hrs_zero_reg_period_1(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    test_data['reg_period_1'][0]['used_hrs'] = 0

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['reg_period_1']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'weigth',
        pd.Series([1, 1]))

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'customer',
        pd.Series(['customer 2', 'customer 3']))


def test_process_data_test_used_hrs_zero_reg_period_2(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    test_data['reg_period_1'][0]['used_hrs'] = 0

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['reg_period_2']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'weigth',
        pd.Series([1, 1]))

    create_table_mock.assert_table_data_column(
        'ubw_customer_per_resource',
        'customer',
        pd.Series(['Entur AS', 'Entur AS']))


def test_process_data_test_dataframe_content_reg_period_1(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['reg_period_1']))

    handler(event, None)

    create_table_mock.assert_table_data(
        'ubw_customer_per_resource',
        pd.DataFrame({
            'reg_period': ['202053', '202053', '202053'],
            'alias': ['frearn', 'frearn', 'einhal'],
            'project_type': ['External Projects', 'Local Projects', 'Local Projects'],
            'work_order': ['work order no 2', 'work order no 1', 'work order no 3'],
            'work_order_description': ['Some work order desc.', 'Some work order desc.', 'Some work order desc.'],
            'customer': ['customer 2', 'customer 1', 'customer 3'],
            'time': [0, 0, 0],
            'weigth': [1, 2, 1],
            'guid': ['b051b402346144a6cdcceb0027f6e80d29019f50',
                     'b051b402346144a6cdcceb0027f6e80d29019f50',
                     '5d79f8b771cd4921b667f9227aece292213806d6', ],
        }))


def test_process_data_test_dataframe_content_reg_period_2(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['reg_period_2']))

    handler(event, None)

    create_table_mock.assert_table_data(
        'ubw_customer_per_resource',
        pd.DataFrame({
            'reg_period': ['202140', '202140'],
            'alias': ['frearn', 'einhal'],
            'project_type': ['External Projects', 'External Projects'],
            'work_order': ['work order no 5', 'work order no 4'],
            'work_order_description': ['Drift, forvalting og support', 'Entur Test'],
            'customer': ['Entur AS', 'Entur AS'],
            'time': [0, 0],
            'weigth': [1, 1],
            'guid': ['b051b402346144a6cdcceb0027f6e80d29019f50',
                     '5d79f8b771cd4921b667f9227aece292213806d6', ],
        }))


def test_process_per_project_data_content_reg_period_1(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=1601294392),
            data=test_data['reg_period_1']))

    handler(event, None)
    create_table_mock.assert_table_data(
        'ubw_per_project_data',
        pd.DataFrame({
            'customer': ['customer 2', 'customer 1', 'customer 3'],
            'employees': [1, 1, 1],
            'hours': np.array([6, 4, 1], dtype=np.float32),
            'reg_period': ["202053", "202053", "202053"],
            'timestamp': [1601294392, 1601294392, 1601294392, ]
        }))


def test_process_per_project_data_content_reg_period_2(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=1601294392),
            data=test_data['reg_period_2']))

    handler(event, None)
    create_table_mock.assert_table_data(
        'ubw_per_project_data',
        pd.DataFrame({
            'customer': ['Entur AS'],
            'employees': [2],
            'hours': np.array([16], dtype=np.float32),
            'reg_period': ["202140"],
            'timestamp': [1601294392]
        }))


def test_process_only_appending_historical_data_reg_period_1(s3_bucket, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=1601294392),
            data=test_data['reg_period_1']))

    handler(event, None)
    handler(event, None)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/ubw_customer_per_resource/_common_metadata',
        'data/test/structured/ubw_customer_per_resource/_metadata',
        'data/test/structured/ubw_customer_per_resource/part.0.parquet',
        'data/test/structured/ubw_per_project_data/_common_metadata',
        'data/test/structured/ubw_per_project_data/_metadata',
        'data/test/structured/ubw_per_project_data/part.0.parquet',
        'data/test/structured/ubw_per_project_data/part.1.parquet'
    ]
    assert len(expected_keys) == len(keys_in_s3)
    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])

def test_process_only_appending_historical_data_reg_period_2(s3_bucket, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=1601294392),
            data=test_data['reg_period_2']))

    handler(event, None)
    handler(event, None)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/ubw_customer_per_resource/_common_metadata',
        'data/test/structured/ubw_customer_per_resource/_metadata',
        'data/test/structured/ubw_customer_per_resource/part.0.parquet',
        'data/test/structured/ubw_per_project_data/_common_metadata',
        'data/test/structured/ubw_per_project_data/_metadata',
        'data/test/structured/ubw_per_project_data/part.0.parquet',
        'data/test/structured/ubw_per_project_data/part.1.parquet'
    ]
    assert len(expected_keys) == len(keys_in_s3)
    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])
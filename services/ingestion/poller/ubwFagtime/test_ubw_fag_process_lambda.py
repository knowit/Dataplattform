from pytest import fixture
from ubw_fag_process_lambda import handler
import pandas as pd
from os import path
from json import load
from dataplattform.common import schema


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


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


def test_process_data(create_table_mock, setup_queue_event, test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'ubw_fagtimer',
        'reg_period',
        pd.Series(['201817', '201907']))


def test_process_data_skip_existing(athena, create_table_mock, setup_queue_event, test_data):
    athena.on_query(
        'SELECT "reg_period" FROM "dev_test_database"."ubw_fagtimer"',
        pd.DataFrame({'reg_period': ['201817']}))

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'ubw_fagtimer',
        'reg_period',
        pd.Series(['201907']))

from googleevent.google_event_process_lambda import handler
from dataplattform.common import schema
from pytest import fixture
import pandas as pd
from os import path
from json import load


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


def test_process_data_table_created(mocker, create_table_mock, setup_queue_event, test_data):
    tmp_data = test_data['data']

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)
    create_table_mock.assert_table_created('google_calendar_events')


def test_process_parquet_get_data(mocker, create_table_mock, setup_queue_event, test_data):
    tmp_data = test_data['data']

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'google_calendar_events',
        'event_id',
        pd.Series(['1235', '1236']))

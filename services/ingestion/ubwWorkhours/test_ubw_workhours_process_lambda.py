from pytest import fixture
from ubw_workhours_process_lambda import handler
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
        'ubw_costumer_per_resource',
        'reg_period',
        pd.Series(['202053', '202053', '202053']))

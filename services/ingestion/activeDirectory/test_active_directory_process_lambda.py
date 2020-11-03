from active_directory_process_lambda import handler
from dataplattform.common import schema
from pytest import fixture
from os import path
from json import load
import pandas as pd


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_data_process.json'), 'r') as json_file:
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


def test_initial_process(setup_queue_event, test_data, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_created(
        'activeDirectory')


def test_process_table_content(setup_queue_event, test_data, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'activeDirectory',
        pd.DataFrame({
            'displayName': ['Per Nordmann'],
            'samAccountName': ['pernord'],
            'company': ['Knowit Objectnet'],
            'knowitBranch': ['Solutions'],
            'isDeleted': False
        }))

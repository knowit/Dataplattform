from dora.dora_process_handler import handler
from dataplattform.common import schema
from pytest import fixture
from json import load
import pandas as pd
from responses import RequestsMock
from os import path

@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs

@fixture
def test_data_poller():
    with open(path.join(path.dirname(__file__), 'test_data/test_data_processing.json'), 'r') as json_file:
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

def test_process_data_poller(setup_queue_event, test_data_poller, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_poller['data']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'github_dora_repos',
        'id',
        pd.Series(["18154316775", "181631654288"]))

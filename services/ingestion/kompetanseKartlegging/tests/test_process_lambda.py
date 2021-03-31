from kompetansekartlegging_process_lambda import handler
from dataplattform.common import schema
from pytest import fixture
from os import path
import json
import pandas as pd
from io import BytesIO


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'ingest.json'), 'r') as json_file:
        yield json.load(json_file)


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


def test_initial_process(setup_queue_event, test_data, create_table_mock, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_created('kompetansekartlegging_employees')

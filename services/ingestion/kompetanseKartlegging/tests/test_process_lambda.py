from kompetansekartlegging_process_lambda import handler
from dataplattform.common import schema
from pytest import fixture
from os import path
import json
import pandas as pd


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data/ingest.json'), 'r') as json_file:
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
    create_table_mock.assert_table_created(
        'kompetansekartlegging_users',
        'kompetansekartlegging_answers',
        'kompetansekartlegging_catalogs',
        'kompetansekartlegging_questions',
        'kompetansekartlegging_categories'
    )


def test_process_users_content(setup_queue_event, test_data, create_table_mock, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_users',
        pd.DataFrame({
            'username': ['2c54bb77-190a-4651-9009-7c9fab39a03a', '3c2af0ad-19f0-4f0d-b6dc-031dfcaa423b'],
            'email': ['per.nordmann@knowit.no', 'kari.nordmann@knowit.no'],
            'guid': ['20dbbfa18380233aa643575720b893fac5137699', '491b9fa9bfac17563882b0fdc6f3a8a97417bd99']
        }))


def test_process_answers_content(setup_queue_event, test_data, create_table_mock, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_answers',
        pd.DataFrame({
            'email': ['per.nordmann@knowit.no'],
            'questionId': ['d1862cf3-7123-4d35-9cfd-6587e97dc0c8'],
            'unanswered': [True],
            'knowledge': [None],
            'motivation': [None],
            'updatedAt': [None],
            'customScaleValue': [None],
            'scaleStart': [None],
            'scaleMiddle': [None],
            'scaleEnd': [None],
            'guid': ['20dbbfa18380233aa643575720b893fac5137699']
        }))
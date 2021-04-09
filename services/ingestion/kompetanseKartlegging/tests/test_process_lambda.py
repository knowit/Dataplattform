from services.ingestion.kompetanseKartlegging.kompetansekartlegging_process_lambda import handler
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
            'email': ['per.nordmann@knowit.no', 'per.nordmann@knowit.no'],
            'question_id': ['46757916-5762-4b29-901c-736f9dca33af', 'e176f891-9e96-42d9-92c8-4b5f726c94f8'],
            'knowledge': [-1.00000, None],
            'motivation': [0.80000, None],
            'customScaleValue': [None, 1.60000],
            'guid': ['20dbbfa18380233aa643575720b893fac5137699', '20dbbfa18380233aa643575720b893fac5137699']
        }))
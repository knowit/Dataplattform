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


@fixture(autouse=True)
def invoke_process_handler(create_table_mock, setup_queue_event, test_data, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']
        )
    )
    return handler(event, None)


def test_initial_process(create_table_mock):
    create_table_mock.assert_table_created(
        'kompetansekartlegging_users',
        'kompetansekartlegging_answers',
        'kompetansekartlegging_catalogs',
        'kompetansekartlegging_questions',
        'kompetansekartlegging_categories'
    )


def test_process_users_content(create_table_mock):
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_users',
        pd.DataFrame({
            'username': ['2c54bb77-190a-4651-9009-7c9fab39a03a', '3c2af0ad-19f0-4f0d-b6dc-031dfcaa423b'],
            'email': ['per.nordmann@knowit.no', 'kari.nordmann@knowit.no'],
            'guid': ['20dbbfa18380233aa643575720b893fac5137699', '491b9fa9bfac17563882b0fdc6f3a8a97417bd99']
        })
    )


def test_process_answers_content(create_table_mock):
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_answers',
        pd.DataFrame({
            'email': ['per.nordmann@knowit.no'],
            'questionId': ['d1862cf3-7123-4d35-9cfd-6587e97dc0c8'],
            'knowledge': [None],
            'motivation': [None],
            'updatedAt': [None],
            'customScaleValue': [None],
            'guid': ['20dbbfa18380233aa643575720b893fac5137699']
        })
    )


def test_process_catalogs_content(create_table_mock):
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_catalogs',
        pd.DataFrame({
            'id': ['fb9e8f06-4cfa-463e-9e8f-cc0853464070', '63371236-3116-4e6d-85aa-168f6d34d18b', None],
            'label': ['2021V', None, 'no_id']
        })
    )


def test_process_categories_content(create_table_mock):
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_categories',
        pd.DataFrame({
            'index': [5, 8],
            'text': ['AI og Data Engineering', 'Smidig metodikk og produktledelse'],
            'description': ['ML og datadrevne loesninger', 'Smidig metodikk og produktledelse'],
            'id': ['84baa82a-bbad-4fed-9bd1-85c9f50fdcfc', 'e99c1908-3da3-4e29-95e9-cfd5bfc41a57']
        })
    )


def test_process_questions_content(create_table_mock):
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_questions',
        pd.DataFrame({
            'index': [92, 76],
            'text': ['Microsoft Azure', 'Rammeverk som tensorflow, keras, pytorch, mm'],
            'id': ['9f40d807-3fa6-4446-bdc2-7681ca136b3b', 'be02bf31-e082-41c9-a9eb-eb4c60c77f8c'],
            'topic': ['Azure', 'ML-rammeverk'],
            'categoryID': ['3efffcf3-b458-467d-bdac-e4ae08b3f040', '84baa82a-bbad-4fed-9bd1-85c9f50fdcfc'],
            'type': ['knowledgeMotivation', 'knowledgeMotivation']
        })
    )

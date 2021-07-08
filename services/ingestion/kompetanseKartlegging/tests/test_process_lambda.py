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
            'username': ['059ef00d-d6af-4517-ad1c-a05c63769c9b', '2f119dc3-02fe-4159-adec-0238d77b18ce'],
            'email': ['fredrik.arnesen@knowit.no', 'einar.halvorsen@knowit.no'],
            'guid': ['b051b402346144a6cdcceb0027f6e80d29019f50', '5d79f8b771cd4921b667f9227aece292213806d6']
        })
    )


def test_process_answers_content(create_table_mock):
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_answers',
        pd.DataFrame({
            'email': ['fredrik.arnesen@knowit.no'],
            'questionId': ['230473f7-37e1-4f69-a106-2bbc01afe5cb'],
            'knowledge': [2.6],
            'motivation': [2.5],
            'updatedAt': ['2021-06-18T12:00:25.553Z'],
            'customScaleValue': [None],
            'guid': ['b051b402346144a6cdcceb0027f6e80d29019f50']
        })
    )


def test_process_catalogs_content(create_table_mock):
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_catalogs',
        pd.DataFrame({
            'id': ['8495bb25-db94-4ef6-9650-3fb46dc252da', 'fb9e8f06-4cfa-463e-9e8f-cc0853464070',
                   '63371236-3116-4e6d-85aa-168f6d34d18b', '603451e8-5f80-4199-82aa-97999cdb4d53'],
            'label': ['test1', '2021V', None, 'ax']
        })
    )


def test_process_categories_content(create_table_mock):
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_categories',
        pd.DataFrame({
            'index': [5, 4],
            'text': ['AI og Data Engineering', 'Backend'],
            'id': ['84baa82a-bbad-4fed-9bd1-85c9f50fdcfc', '5faf0519-809d-4d02-a8a0-9862024170bc']
        })
    )


def test_process_questions_content(create_table_mock):
    create_table_mock.assert_table_data_contains_df(
        'kompetansekartlegging_questions',
        pd.DataFrame({
            'index': [116, 43],
            'text': ['Programmering mot ESP32/ ESP8266 ved bruk av IDF eller Arduinorammeverket',
                     'Minst en kjøreomgivelse (runtime environment) basert på Javascript (Node, Deno)'],
            'id': ['d1862cf3-7123-4d35-9cfd-6587e97dc0c8', 'aed2b4ec-dc31-4236-a97d-2b840536373d'],
            'topic': ['ESP32', 'Kjøreomgivelser'],
            'categoryID': ['a79de551-d88e-40c6-808f-ce0d2d07a242', 'b76e0d72-aeab-4cd2-9278-c64ec3314b4c'],
            'type': ['knowledgeMotivation', 'knowledgeMotivation'],
            'scaleStart': [None, None],
            'scaleEnd': [None, None],
            'scaleMiddle': [None, None]
        })
    )

from knowit_labs_process_lambda import handler
from dataplattform.common import schema
from responses import RequestsMock
from pytest import fixture
from os import path
from json import load
import pandas as pd


@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs


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


def test_process_data(setup_queue_event, test_data, create_table_mock):
    tmp_data = test_data['data']

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'blog_posts',
        'medium_id',
        pd.Series(['asdf', '1234']))


def test_process_data_skip_existing(setup_queue_event, test_data, athena, create_table_mock):
    tmp_data = test_data['data']

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    athena.on_query(
        'SELECT "medium_id" FROM "dev_test_database"."blog_posts"',
        pd.DataFrame({'medium_id': ['asdf']}))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'blog_posts',
        'medium_id',
        pd.Series(['1234']))

    create_table_mock.assert_table_data_column(
        'blog_updates',
        'medium_id',
        pd.Series(['asdf', '1234']))

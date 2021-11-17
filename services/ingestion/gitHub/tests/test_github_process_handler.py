from github.github_process_handler import handler
from dataplattform.common import schema
from pytest import fixture
from json import load
import pandas as pd
from os import path


@fixture
def test_data_poller():
    with open(path.join(path.dirname(__file__), 'test_data/test_process_poller_data.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data_webhook():
    with open(path.join(path.dirname(__file__), 'test_data/test_process_webhook_data.json'), 'r') as json_file:
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
        'github_knowit_repos',
        'id',
        pd.Series([4672898, 4730463]))


def test_process_data_webhook(setup_queue_event, test_data_webhook, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_webhook['data']))

    handler(event, None)

    create_table_mock.assert_table_data_contains_df(
        'github_knowit_repo_status', pd.DataFrame({
                'id': [186853002],
                'updated_at': [1557933641],
                'pushed_at': [1557933652],
                'forks_count': [1],
                'stargazers_count': [0]
            }))


def test_process_data_skip_existing(setup_queue_event, athena, test_data_poller, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_poller['data']))

    athena.on_query(
        'SELECT "id" FROM "github_knowit_repos"',
        pd.DataFrame({'id': [4672898]}))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'github_knowit_repos',
        'id',
        pd.Series([4730463]))

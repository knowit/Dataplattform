from jirasales.jira_process_lambda import handler
from dataplattform.common import schema
from json import load
import pandas as pd
from pytest import fixture
from os import path


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


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


def test_handler_process(setup_queue_event, test_data, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=test_data['metadata'],
            data=test_data['data']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'jira_issue_created',
        'issue_status',
        pd.Series(['Open']))

    create_table_mock.assert_table_data_column(
        'jira_issue_created',
        'customer',
        pd.Series(['Test Testerson']))

from slack_webhook_process_lambda import handler
from dataplattform.common import schema
from json import load
from os import path
from pytest import fixture
import pandas as pd


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
def test_message_data_event():
    with open(path.join(path.dirname(__file__), 'test_message_event.json'), 'r') as json_file:
        yield load(json_file)


def test_process_data(setup_queue_event,
                      create_table_mock,
                      test_message_data_event):

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_message_data_event['data']))

    handler(event, None)

    expected_df = pd.DataFrame({
                'event_type': ['message'],
                'channel': ['C2147483705'],
                'channel_name': ['Test'],
                'event_ts': [1234567890],
                'team_id': ['TXXXXXXXX'],
                'emoji': ['thumbsup'],
            })

    create_table_mock.assert_table_data_contains_df('slack_emoji', expected_df)

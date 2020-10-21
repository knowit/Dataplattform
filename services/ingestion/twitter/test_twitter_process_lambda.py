from twitter_process_lambda import handler
from dataplattform.common import schema
from pytest import fixture
from datetime import datetime, timezone
from unittest.mock import Mock
from os import path
from json import load
import pandas as pd


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data2():
    with open(path.join(path.dirname(__file__), 'test_data2.json'), 'r') as json_file:
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


def mock_twitter_model(data):
    m = Mock()
    m.configure_mock(**data)  # Have to use `configure_mock` to support name attribute
    return m


@fixture(autouse=True)
def mock_twitter_api(mocker):
    api = mocker.patch('twitter_ingest_lambda.API')
    yield api.return_value


user_data = {
    'id': 1234,
    'screen_name': 'test_testerson',
    'name': 'Test Testerson',
    'statuses_count': 1,
    'followers_count': 1,
    'favourites_count': 1,
    'friends_count': 1,
    'listed_count': 1
}

search_data = {
    'id': 1234,
    'created_at':  datetime(2020, 1, 1, tzinfo=timezone.utc),
    'full_text': 'asdf',
    'favorite_count': 1,
    'retweet_count': 1,
    'lang': 'no',
    'entities': {
        'hashtags': [],
    },
    'place': None,
    'in_reply_to_screen_name': None
}

timeline_data = {
    'id': 1234,
    'created_at': datetime(2020, 1, 1, tzinfo=timezone.utc),
    'full_text': 'asdf',
    'favorite_count': 1,
    'retweet_count': 1,
    'lang': 'no',
    'entities': {
        'hashtags': [],
        'user_mentions': []
    },
    'user': mock_twitter_model({
        'screen_name': 'asdf',
        'name': 'sdf'
    })
}


def test_process_data(create_table_mock, setup_queue_event, test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)

    create_table_mock.assert_table_created(
        'twitter_tweets',
        'twitter_timeline',
        'twitter_account_status_update')


def test_process_parquet_get_user_data(create_table_mock, setup_queue_event, test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'twitter_account_status_update',
        'user_id',
        pd.Series([1234, 1234, 1234, 1234]))


def test_process_parquet_search_data(create_table_mock, setup_queue_event, test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)

    create_table_mock.assert_table_data(
        'twitter_tweets',
        pd.DataFrame({
            'tweet_id': [1234],
            'created_at': [1577836800],
            'text': ['asdf'],
            'is_retweet': [False],
            'favorite_count': [1],
            'retweet_count': [1],
            'language': ['no'],
            'hashtags': [None],
            'place': [None],
            'reply_to': [None]
        }))


def test_process_parquet_user_timeline_data(create_table_mock, setup_queue_event, test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)

    create_table_mock.assert_table_data(
        'twitter_timeline',
        pd.DataFrame({
            'tweet_id': [1234],
            'created_at': [1577836800],
            'user_screen_name': ['asdf'],
            'text': ['asdf'],
            'is_retweet': [False],
            'favorite_count': [1],
            'retweet_count': [1],
            'language': ['no'],
            'hashtags': [None],
            'mentions': [None],
            'user_name': ['sdf'],
        }))


def test_process_parquet_search_data_skip_existing(athena, create_table_mock, setup_queue_event, test_data2):
    athena.on_query(
        'SELECT "tweet_id" FROM "dev_test_database"."twitter_tweets"',
        pd.DataFrame({'tweet_id': [1234]}))
    athena.on_query(
        'SELECT "tweet_id" FROM "dev_test_database"."twitter_timeline"',
        pd.DataFrame({'tweet_id': [1234]}))

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data2['data']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'twitter_tweets',
        'tweet_id',
        pd.Series([4321]))

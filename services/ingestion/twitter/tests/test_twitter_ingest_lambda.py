from twitter.twitter_ingest_lambda import handler
from pytest import fixture
from json import loads
from datetime import datetime, timezone
from unittest.mock import Mock


def mock_twitter_model(data):
    m = Mock()
    m.configure_mock(**data)  # Have to use `configure_mock` to support name attribute
    return m


@fixture(autouse=True)
def mock_twitter_api(mocker):
    api = mocker.patch('twitter.twitter_ingest_lambda.API')
    yield api.return_value


@fixture
def mock_twitter_data(mock_twitter_api):
    def mock_data(method, mock_data, *_mock_data, pageable=False):
        if not pageable:
            getattr(mock_twitter_api, method).return_value = mock_twitter_model(mock_data)
        else:
            def mock_generator():
                yield [mock_twitter_model(d) for d in [mock_data] + list(_mock_data)]
                yield []
            getattr(mock_twitter_api, method).pagination_mode = 'page'
            getattr(mock_twitter_api, method).side_effect = mock_generator()

    yield mock_data


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


def test_handler_data(s3_bucket, mock_twitter_data):
    mock_twitter_data('get_user', user_data)
    mock_twitter_data('search', search_data, pageable=True)
    mock_twitter_data('user_timeline', timeline_data, pageable=True)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert all(key in data['data'].keys() for key in ['search', 'timeline', 'accounts']) and \
        len(data['data']['search']) == 1 and len(data['data']['timeline']) == 1 and len(data['data']['accounts']) == 4


def test_handler_get_user_data(s3_bucket, mock_twitter_data):
    mock_twitter_data('get_user', user_data)
    mock_twitter_data('search', search_data, pageable=True)
    mock_twitter_data('user_timeline', timeline_data, pageable=True)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())['data']['accounts']

    expected = {
        'user_id': 1234,
        'screen_name': 'test_testerson',
        'name': 'Test Testerson',
        'statuses_count': 1,
        'followers_count': 1,
        'favourites_count': 1,
        'friends_count': 1,
        'listed_count': 1}

    assert all([expected == d for d in data]) and len(data) == 4


def test_handler_search_data(s3_bucket, mock_twitter_data):
    mock_twitter_data('get_user', user_data)
    mock_twitter_data(
        'search',
        search_data,
        {
            'id': 4321,
            'created_at':  datetime(2020, 1, 1, tzinfo=timezone.utc),
            'full_text': 'RT @ asdf',
            'favorite_count': 1,
            'retweet_count': 1,
            'lang': 'no',
            'entities': {
                'hashtags': [{'text': 'emneknagg1'}, {'text': 'emneknagg2'}],
            },
            'place': mock_twitter_model({
                'full_name': 'some place'
            }),
            'in_reply_to_screen_name': 'knowitnorge'
        },
        pageable=True)
    mock_twitter_data('user_timeline', timeline_data, pageable=True)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())['data']['search']

    expected = [
        {
            'tweet_id': 1234,
            'created_at': 1577836800,
            'text': 'asdf',
            'is_retweet': False,
            'favorite_count': 1,
            'retweet_count': 1,
            'language': 'no',
            'hashtags': None,
            'place': None,
            'reply_to': None
        },
        {
            'tweet_id': 4321,
            'created_at': 1577836800,
            'text': 'RT @ asdf',
            'is_retweet': True,
            'favorite_count': 1,
            'retweet_count': 1,
            'language': 'no',
            'hashtags': 'emneknagg1;emneknagg2',
            'place': 'some place',
            'reply_to': 'knowitnorge'
        }]

    assert len(data) == 2 and all([d == expected[i] for i, d in enumerate(data)])


def test_handler_user_timeline_data(s3_bucket, mock_twitter_data):
    mock_twitter_data('get_user', user_data)
    mock_twitter_data('search', search_data, pageable=True)
    mock_twitter_data(
        'user_timeline',
        timeline_data,
        {
            'id': 1234,
            'created_at': datetime(2020, 1, 1, tzinfo=timezone.utc),
            'full_text': 'RT @ asdf',
            'favorite_count': 1,
            'retweet_count': 1,
            'lang': 'no',
            'entities': {
                'hashtags': [{'text': 'emneknagg'}],
                'user_mentions': [{'screen_name': 'test testermann'}],
            },
            'user': mock_twitter_model({
                'screen_name': 'asdf',
                'name': 'sdf'
            })
        },
        pageable=True)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())['data']['timeline']

    expected = [
        {
            'tweet_id': 1234,
            'created_at': 1577836800,
            'user_screen_name': 'asdf',
            'text': 'asdf',
            'is_retweet': False,
            'favorite_count': 1,
            'retweet_count': 1,
            'language': 'no',
            'hashtags': None,
            'mentions': None,
            'user_name': 'sdf'
        },
        {
            'tweet_id': 1234,
            'created_at': 1577836800,
            'user_screen_name': 'asdf',
            'text': 'RT @ asdf',
            'is_retweet': True,
            'favorite_count': 1,
            'retweet_count': 1,
            'language': 'no',
            'hashtags': 'emneknagg',
            'mentions': 'test testermann',
            'user_name': 'sdf'
        }]

    assert len(data) == 2 and all([d == expected[i] for i, d in enumerate(data)])

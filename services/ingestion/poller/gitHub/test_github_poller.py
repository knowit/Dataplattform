from github_poller import handler, url
from os import environ
from pytest import fixture
from json import loads
from responses import RequestsMock, GET


@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs


def test_handler_data_in_s3(s3_bucket, mocked_responses):
    mocked_responses.add(GET, url, json=[{}], status=200)

    handler(None, None)

    s3_object_summary = next(iter(s3_bucket.objects.all()), None)
    assert s3_object_summary is not None


def test_handler_key_format(s3_bucket, mocked_responses):
    mocked_responses.add(GET, url, json=[{}], status=200)

    handler(None, None)

    s3_object_summary = next(iter(s3_bucket.objects.all()))
    assert s3_object_summary.key.startswith(environ.get('ACCESS_PATH')) and\
        s3_object_summary.key.endswith('.json')


def test_handler_metadata(s3_bucket, mocked_responses):
    mocked_responses.add(GET, url, json=[{}], status=200)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert 'timestamp' in data['metadata'] and\
        'event' in data['metadata'] and\
        data['metadata']['event'] == 'repo'


def test_handler_data(s3_bucket, mocked_responses):
    some_github_data = {
        'key': 'value'
    }
    mocked_responses.add(GET, url, json=[some_github_data], status=200)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['data'][0]['key'] == some_github_data['key']


def test_handler_follow_links(s3_bucket, mocked_responses):
    some_github_data = {
        'key': 'value1'
    }
    some_extra_github_data = {
        'key': 'value2'
    }
    follow_link = 'http://mock.link'
    mocked_responses.add(GET, url, json=[some_github_data], headers={'Link': f'{follow_link}; rel="next"'}, status=200)
    mocked_responses.add(GET, follow_link, json=[some_extra_github_data], status=200)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['data'][0]['key'] == some_github_data['key'] and\
        data['data'][1]['key'] == some_extra_github_data['key']

from github_poller_ingest_handler import handler, url
from pytest import fixture
from json import loads, load
from responses import RequestsMock, GET
from os import path


@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data_poller.json'), 'r') as json_file:
        yield load(json_file)


def test_handler_follow_links(s3_bucket, mocked_responses, test_data):
    some_github_data, some_extra_github_data = test_data

    follow_link = 'http://mock.link'
    mocked_responses.add(GET, url, json=[some_github_data], headers={'Link': f'{follow_link}; rel="next"'}, status=200)
    mocked_responses.add(GET, follow_link, json=[some_extra_github_data], status=200)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['data'][0]["name"] == "Ky.yr" and data['data'][1]["name"] == "knowit.github.com"


def test_handler_data_content(s3_bucket, mocked_responses, test_data):
    mocked_responses.add(GET, url, json=test_data, status=200)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    expected = {
        "id": 4672898,
        "name": "Ky.yr",
        "owner": "knowit",
        "html_url": "https://github.com/knowit/Ky.yr",
        "description": "Knowit Reaktor Kyber - Umbraco Yr weather integration",
        "url": "https://api.github.com/repos/knowit/Ky.yr",
        "created_at": 1339748161,
        "updated_at": 1545134854,
        "pushed_at": 1339759327,
        "stargazers_count": 2,
        "language": "C#",
        "forks_count": 0,
        "default_branch": "master",
    }
    assert all([data['data'][0][k] == v for k, v in expected.items()])

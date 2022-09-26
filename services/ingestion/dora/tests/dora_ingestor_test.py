from dora.dora_ingestion_handler import handler
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
    with open(path.join(path.dirname(__file__), 'test_data/test_data_github_events.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_defaultbranch_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_data_defaultBranch.json'), 'r') as json_file:
        yield load(json_file)


def test_handler_data_content(s3_bucket, mocked_responses, test_data, test_defaultbranch_data):
    mocked_responses.add(GET, 'https://api.github.com/repos/knowit/Dataplattform/events', json=test_data, status=200)
    mocked_responses.add(
        GET,
        'https://api.github.com/repos/knowit/dataplattform',
        json=test_defaultbranch_data, status=200)

    handler(None, None)
    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    expected = {
        "id": '18916884826',
        "name": "knowit/Dataplattform",
        "type": "PullRequestEvent",
        "merged_at": 1637092191,
        "created_at": 1637069576,
        "base-ref": "develop",
        "default_branch": "develop",
        "source": "github",
    }
    assert all([data['data'][0][k] == v for k, v in expected.items()])

from kompetansekartlegging_ingest_lambda import handler, base_url
from pytest import fixture
from responses import RequestsMock, GET
from json import loads
from os import path


@fixture
def test_answers_data():
    with open(path.join(path.dirname(__file__), 'test_answers_data.json'), 'r') as f:
        yield f.read()


@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs


def test_response(mocked_responses, test_answers_data):
    mocked_responses.add(GET, f'{base_url}/answers', body=test_answers_data, status=200)

    data = handler(None)
    assert data is not None

from kompetansekartlegging_ingest_lambda import handler
from json import loads
from pytest import fixture
from responses import RequestsMock, GET
from os import path
import re


@fixture
def test_answers_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_answers_data.json'), 'r') as f:
        yield f.read()


@fixture
def test_catalogs_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_catalogs_data.json'), 'r') as f:
        yield f.read()


@fixture
def test_categories_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_categories_data.json'), 'r') as f:
        yield f.read()


@fixture
def test_questions_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_questions_data.json'), 'r') as f:
        yield f.read()


@fixture
def test_users_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_users_data.json'), 'r') as f:
        yield f.read()


@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs


def test_initial_ingest(mocked_responses,
                        test_answers_data,
                        test_users_data,
                        test_catalogs_data,
                        test_categories_data,
                        test_questions_data,
                        s3_bucket):
    base_url = 'https://api.kompetanse.knowit.no/dev'

    # add mocked responses
    mocked_responses.add(GET, f'{base_url}/users', body=test_users_data, status=200)
    mocked_responses.add(GET, f'{base_url}/answers', body=test_answers_data, status=200)
    mocked_responses.add(GET, f'{base_url}/catalogs', body=test_catalogs_data, status=200)
    mocked_responses.add(GET, re.compile(f'{base_url}/catalogs/.*?/categories'), body=test_categories_data, status=200)
    mocked_responses.add(GET, re.compile(f'{base_url}/catalogs/.*?/questions'), body=test_questions_data, status=200)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    data = data['data']

    assert data['users'] is not None
    assert data['answers'] is not None
    assert data['catalogs'] is not None
    assert data['categories'] is not None
    assert data['questions'] is not None

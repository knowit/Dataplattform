from jwtAuthenticator import handler
from json import load
from os import path
from pytest import fixture


@fixture
def event():
    with open(path.join(path.dirname(__file__), 'test_data/test_data.json'), 'r') as json_file:
        yield load(json_file)


def test_missing_token(event):
    event['Records'][0]['cf']['request']['headers'].pop('authorization')
    response = handler(event, None)
    assert response['status'] == 401

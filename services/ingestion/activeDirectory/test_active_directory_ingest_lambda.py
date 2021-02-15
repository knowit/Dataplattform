from active_directory_ingest_lambda import handler
from pytest import fixture
from json import load
from os import path
import responses


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_data_ingest.json'), 'r') as json_file:
        yield load(json_file)


def make_test_json(user_details):
    return [
        {
            'userDetails': user_detail
        } for user_detail in user_details
    ]


def test_initial_ingest(s3_bucket, test_data, dynamodb_resource):
    responses.add(responses.GET, 'http://10.205.0.5:20201/api/Users', json=make_test_json(test_data), status=200)
    handler(None, None)

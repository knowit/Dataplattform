from google_forms_webhook import handler
from dataplattform.testing.events import APIGateway
from json import loads
from os import path
from pytest import fixture
import pandas as pd


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield json_file.read()


def test_insert_data(s3_bucket, test_data, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data is not None




from google_forms_webhook import handler
from dataplattform.testing.events import APIGateway
from json import loads
from os import path
from pytest import fixture
import pandas as pd


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data_single_respondent.json'), 'r') as json_file:
        yield json_file.read()

@fixture
def test_data_mulitple():
    with open(path.join(path.dirname(__file__), 'test_data_multiple_choice.json'), 'r') as json_file:
        yield json_file.read()


def test_insert_data(s3_bucket, test_data, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data is not None


def test_insert_data_mult(s3_bucket, test_data_mulitple, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data_mulitple).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data is not None

from google_sheets_webhook import handler
from dataplattform.testing.events import APIGateway
from json import loads
from hmac import new
from hashlib import sha1
from os import path
from pytest import fixture
import pandas as pd
from pandas.testing import assert_frame_equal


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data1.json'), 'r') as json_file:
        yield json_file.read()


def test_insert_data(s3_bucket, test_data):
    handler(APIGateway(
        headers={},
        body=test_data).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    print("In test file", data)

    assert True


def test_process_parquet_get_data(mocker, create_table_mock, test_data):    
    handler(APIGateway(
        headers={},
        body=test_data).to_dict(), None)

    create_table_mock.assert_table_data_column(
        'google_sheets_metadata',
        'author',
        pd.Series(['test@test.b']))


# TODO: Filtrere bort blanke rader/kolonner
# TODO: Test metadata
# TODO: 

from googlesheets.google_sheets_webhook_ingest_lambda import handler as ingest_handler
from dataplattform.testing.events import APIGateway
from json import loads
from os import path
from pytest import fixture


@fixture
def test_data1():
    with open(path.join(path.dirname(__file__), 'test_data1.json'), 'r') as json_file:
        yield json_file.read()


def test_insert_data_ingest(s3_bucket, test_data1):
    ingest_handler(APIGateway(
        headers={},
        body=test_data1).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data']['tableName'] == 'enkel_test_ark 1'

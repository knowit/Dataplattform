from google_forms_ingest_lambda import handler as ingestHandler
from dataplattform.testing.events import APIGateway
import os
from json import loads
from pytest import fixture


@fixture
def test_data_quiz():
    with open(os.path.join(os.path.dirname(__file__),
              'test_data_files/test_data_quiz_single_respondent_valid_types.json'), 'r') as json_file:
        yield json_file.read()


def test_insert_data_quiz_ingest(s3_bucket, test_data_quiz):
    ingestHandler(APIGateway(
        headers={},
        body=test_data_quiz).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    print(data)
    assert data['data']['tableName'] == 'test_quiz'

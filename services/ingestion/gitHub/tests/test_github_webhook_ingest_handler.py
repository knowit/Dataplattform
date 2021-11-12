from github.github_webhook_ingest_handler import handler
from dataplattform.testing.events import APIGateway
from json import loads
from hmac import new
from hashlib import sha1
from os import path
from pytest import fixture


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_webhook_ingest_data.json'), 'r') as json_file:
        yield json_file.read()


def test_invalid_no_signature():
    res = handler(APIGateway().to_dict(), None)

    assert res['statusCode'] == 403


def test_invalid_bogus_signature():
    headers = {
        'X-Hub-Signature': 'sha1=asdf',
        'X-GitHub-Event': 'test'
    }
    res = handler(APIGateway(headers=headers).to_dict(), None)

    assert res['statusCode'] == 403


def test_valid_signature(test_data):
    signature = new('iamsecret'.encode(), test_data.encode(), sha1).hexdigest()
    headers = {
        'X-Hub-Signature': f'sha1={signature}',
        'X-GitHub-Event': 'test'
    }
    res = handler(APIGateway(headers=headers, body=test_data).to_dict(), None)

    assert res['statusCode'] == 200


def test_insert_data(s3_bucket, test_data):
    signature = new('iamsecret'.encode(), test_data.encode(), sha1).hexdigest()
    handler(APIGateway(
        headers={
            'X-Hub-Signature': f'sha1={signature}',
            'X-GitHub-Event': 'test'
            },
        body=test_data).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    print(data)

    assert data['metadata']['event'] == 'test' and\
        data['data']['id'] == 186853002

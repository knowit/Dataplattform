from github_webhook import handler
from dataplattform.testing.events import APIGateway
from json import loads, dumps
from hmac import new
from hashlib import sha1


def test_invalid_no_signature():
    res = handler(APIGateway().to_dict(), None)

    assert res['statusCode'] == 403 and\
        loads(res['body'])['reason'] == 'No signature'


def test_invalid_bogus_signature():
    res = handler(APIGateway(headers={'X-Hub-Signature': 'sha1=asdf'}).to_dict(), None)

    assert res['statusCode'] == 403 and\
        loads(res['body'])['reason'] == 'Invalid signature'


def test_valid_signature():
    data = dumps({'repository': {'private': True}})
    signature = new('iamsecret'.encode(), data.encode(), sha1).hexdigest()
    res = handler(APIGateway(headers={'X-Hub-Signature': f'sha1={signature}'}, body=data).to_dict(), None)

    assert res['statusCode'] == 200


def test_insert_data(s3_bucket):
    test_data = dumps({'repository': {'private': False, 'test': 123}})
    signature = new('iamsecret'.encode(), test_data.encode(), sha1).hexdigest()
    handler(APIGateway(
        headers={
            'X-Hub-Signature': f'sha1={signature}',
            'X-GitHub-Event': 'test'
            },
        body=test_data).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['metadata']['event'] == 'test' and\
        data['data']['repository']['test'] == 123

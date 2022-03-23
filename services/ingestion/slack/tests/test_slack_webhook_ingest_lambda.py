from slack.slack_webhook_ingest_lambda import handler

from dataplattform.testing.events import APIGateway
from json import loads, dumps
from hmac import new
from hashlib import sha256
from os import path
from pytest import fixture
from responses import RequestsMock, GET


@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs


@fixture
def test_reaction_data():
    with open(path.join(path.dirname(__file__), 'test_reaction_data.json'), 'r') as json_file:
        yield json_file.read()


@fixture
def test_message_data():
    with open(path.join(path.dirname(__file__), 'test_message_data.json'), 'r') as json_file:
        yield json_file.read()


def test_invalid_no_signature():
    res = handler(APIGateway().to_dict(), None)

    assert res['statusCode'] == 403


def test_invalid_bogus_signature():
    res = handler(APIGateway(headers={
        'X-Slack-Signature': 'asdf',
        'X-Slack-Request-Timestamp': '0'
        }).to_dict(), None)

    assert res['statusCode'] == 403


def test_valid_signature():
    data = dumps({'type': '', 'event': {'type': ''}})

    sig_string = f'v0:0:{data}'.encode()
    signature = new('iamsecret'.encode(), sig_string, sha256).hexdigest()

    res = handler(APIGateway(headers={
        'X-Slack-Signature': f'v0={signature}',
        'X-Slack-Request-Timestamp': '0'
        },
        body=data).to_dict(), None)

    assert res['statusCode'] == 200


def test_insert_reaction_data(s3_bucket, mocked_responses, test_reaction_data):
    sig_string = f'v0:0:{test_reaction_data}'.encode()
    signature = new('iamsecret'.encode(), sig_string, sha256).hexdigest()

    mocked_responses.add(GET, 'https://slack.com/api/channels.info', json={'channel': {'name': 'Test'}}, status=200)

    handler(APIGateway(headers={
        'X-Slack-Signature': f'v0={signature}',
        'X-Slack-Request-Timestamp': '0'
        },
        body=test_reaction_data).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['data'][0]['emoji'] == 'thumbsup' and \
        data['data'][0]['event_type'] == 'reaction_added'


def test_insert_message_data(s3_bucket, mocked_responses, test_message_data):
    sig_string = f'v0:0:{test_message_data}'.encode()
    signature = new('iamsecret'.encode(), sig_string, sha256).hexdigest()

    mocked_responses.add(GET, 'https://slack.com/api/channels.info', json={'channel': {'name': 'Test'}}, status=200)

    handler(APIGateway(headers={
        'X-Slack-Signature': f'v0={signature}',
        'X-Slack-Request-Timestamp': '0'
        },
        body=test_message_data).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data'][0]['emoji'] == 'thumbsup' and \
        data['data'][0]['event_type'] == 'message'

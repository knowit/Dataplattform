from slack_webhook import handler
from dataplattform.testing.events import APIGateway
from json import loads, dumps
from hmac import new
from hashlib import sha256


def test_invalid_no_signature():
    res = handler(APIGateway().to_dict(), None)

    assert res['statusCode'] == 403 and\
        loads(res['body'])['reason'] == 'No signature'


def test_invalid_bogus_signature():
    res = handler(APIGateway(headers={
        'X-Slack-Signature': 'asdf',
        'X-Slack-Request-Timestamp': '0'
        }).to_dict(), None)

    assert res['statusCode'] == 403 and\
        loads(res['body'])['reason'] == 'Invalid signature'


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


def test_insert_data(s3_bucket, mocker):
    mocker.patch('filter.get_channel_name', return_value='test')

    data = dumps({
        'type': '',
        'event': {
            'type': '',
            'channel': 'CSomething'
            }
        })

    sig_string = f'v0:0:{data}'.encode()
    signature = new('iamsecret'.encode(), sig_string, sha256).hexdigest()

    handler(APIGateway(headers={
        'X-Slack-Signature': f'v0={signature}',
        'X-Slack-Request-Timestamp': '0'
        },
        body=data).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['data']['event']['channel'] == 'CSomething'

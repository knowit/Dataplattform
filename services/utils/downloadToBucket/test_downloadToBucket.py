from downloadToBucket import handler
from pytest import fixture
from dataplattform.testing.utilities import FakeResponse
from os import path
from json import load
from mock import patch


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


def test_handler_private_bucket(test_data, s3_private_bucket):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        event = {}
        test_data['private'] = True
        event["body"] = test_data
        handler(event, None)
        response = s3_private_bucket.Object(next(iter(s3_private_bucket.objects.all())).key).get()
        data = response['Body']
        assert data is not None


def test_handler_public_bucket(test_data, s3_public_bucket):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        event = {}
        test_data['private'] = False
        event["body"] = test_data
        handler(event, None)
        response = s3_public_bucket.Object(next(iter(s3_public_bucket.objects.all())).key).get()
        data = response['Body']
        assert data is not None

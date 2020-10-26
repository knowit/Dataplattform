from downloadToPublicBucket import handler
from pytest import fixture
from dataplattform.testing.plugin import FakeResponse
from os import path, environ
from json import load
from mock import patch


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


def test_handler(test_data, s3_public_bucket):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        event = {}
        test_data['bucket'] = environ['PUBLIC_BUCKET']
        event["body"] = test_data
        handler(event, None)
        response = s3_public_bucket.Object(next(iter(s3_public_bucket.objects.all())).key).get()
        data = response['Body']
        assert data is not None

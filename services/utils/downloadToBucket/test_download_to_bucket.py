from dataplattform.testing.utilities import FakeResponse
from download_to_bucket import handler
from pytest import fixture
from os import path
from json import load
from mock import patch


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


def test_handler_private_bucket(test_data, s3_private_bucket):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        test_data['private'] = True
        event = test_data
        handler(event, None)
        response = s3_private_bucket.Object(next(iter(s3_private_bucket.objects.all())).key).get()
        data = response['Body']
        assert data is not None


def test_handler_public_bucket(test_data, s3_public_bucket):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        test_data['private'] = False
        event = test_data
        handler(event, None)
        response = s3_public_bucket.Object(next(iter(s3_public_bucket.objects.all())).key).get()
        data = response['Body']
        assert data is not None


def test_handler_invalid_url(test_data):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        test_data['body']['requestUrl'] = ''
        r = handler(test_data, None)
        assert r == 400


def test_handler_invalid_filetype(test_data):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        test_data['filetype'] = 'html'
        r = handler(test_data, None)
        assert r == 400


def test_download_from_http_mismatch_content_type(test_data):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        test_data['filetype'] = 'docx'
        r = handler(test_data, None)
        assert r == 400


def test_download_from_http_not_readable(test_data):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=None, readable=False)):
        r = handler(test_data, None)
        assert r == 400

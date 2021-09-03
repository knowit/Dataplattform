from dataplattform.testing.utilities import FakeResponse, FakePngResponse
from download_to_bucket import handler
from pytest import fixture
from os import path
from json import load
from mock import patch


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


def test_handler_public_bucket(test_data, s3_public_bucket):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        test_data['pdf']['private'] = False
        event = test_data['pdf']
        handler(event, None)
        response = s3_public_bucket.Object(next(iter(s3_public_bucket.objects.all())).key).get()
        data = response['Body']
        assert data is not None


def test_handler_invalid_url(test_data):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        test_data['pdf']['body']['requestUrl'] = ''
        r = handler(test_data['pdf'], None)
        assert r == 400


def test_handler_invalid_filetype(test_data):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        test_data['pdf']['filetype'] = 'html'
        r = handler(test_data['pdf'], None)
        assert r == 400


def test_download_from_http_mismatch_content_type(test_data):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}')):
        test_data['pdf']['filetype'] = 'docx'
        r = handler(test_data['pdf'], None)
        assert r == 400


def test_download_from_http_not_readable(test_data):
    with patch('urllib.request.urlopen', return_value=FakeResponse(data=None, readable=False)):
        r = handler(test_data['pdf'], None)
        assert r == 400


def test_handler_for_png(test_data, s3_public_bucket):
    with patch('urllib.request.urlopen', return_value=FakePngResponse(data=b'{}')):
        test_data['png']['private'] = False
        event = test_data['png']
        handler(event, None)
        response = s3_public_bucket.Object(next(iter(s3_public_bucket.objects.all())).key).get()
        data = response['Body']
        assert data is not None

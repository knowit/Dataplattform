from dataplattform.common.helper import download_from_http, save_document
from dataplattform.testing.utilities import FakeResponse
from os import environ
from pytest import fixture


@fixture(autouse=True)
def test_httpRequest():
    body = {'filetype': 'pdf', 'requestUrl': 'http://test_url.com',
            'filename': 'test.pdf', 'bucket': environ.get('PRIVATE_BUCKET')}
    yield body


@fixture
def mock_urlopen(mocker):
    yield mocker.patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}'))


@fixture(autouse=True)
def mock_launch_async_lambda(mocker):
    yield mocker.patch('dataplattform.common.helper.launch_async_lambda')


def test_download_from_http_base_case(s3_private_bucket, test_httpRequest, mock_urlopen):
    r = download_from_http(test_httpRequest)
    assert r == 200
    response = s3_private_bucket.Object(next(iter(s3_private_bucket.objects.all())).key).get()
    assert response['Body'] is not None


def test_download_from_http_invalid_filetype(test_httpRequest, mock_urlopen):
    test_httpRequest['filetype'] = 'html'

    r = download_from_http(test_httpRequest)
    assert r == 400


def test_download_from_http_mismatch_content_type(test_httpRequest, mock_urlopen):
    test_httpRequest['filetype'] = 'docx'
    r = download_from_http(test_httpRequest)
    assert r == 400


def test_download_from_http_not_readable(test_httpRequest, mock_urlopen):
    mock_urlopen.return_value = FakeResponse(data=None, readable=False)
    r = download_from_http(test_httpRequest)
    assert r == 400


def test_save_document(test_httpRequest, mock_urlopen):
    key = save_document(test_httpRequest)
    assert "test.pdf" == key

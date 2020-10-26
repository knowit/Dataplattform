from dataplattform.common.helper import Helper
from dataplattform.testing.plugin import FakeResponse
from os import environ
from pytest import fixture


@fixture(autouse=True)
def test_data():
    body = {'filetype': 'pdf', 'requestUrl': 'http://test_url.com',
            'filename': 'test.pdf', 'bucket': environ.get('PRIVATE_BUCKET')}
    yield body


@fixture
def mock_urlopen(mocker):
    yield mocker.patch('urllib.request.urlopen', return_value=FakeResponse(data=b'{}'))


def test_download_from_http_base_case(s3_private_bucket, test_data, mock_urlopen):
    r = Helper().download_from_http(body=test_data)
    assert r == 200
    response = s3_private_bucket.Object(next(iter(s3_private_bucket.objects.all())).key).get()
    assert response['Body'] is not None


def test_download_from_http_invalid_filetype(s3_private_bucket, test_data, mock_urlopen):
    test_data['filetype'] = 'html'

    r = Helper().download_from_http(body=test_data)
    assert r == 400


def test_download_from_http_mismatch_content_type(s3_private_bucket, test_data, mock_urlopen):
    test_data['filetype'] = 'docx'
    r = Helper().download_from_http(body=test_data)
    assert r == 400


def test_download_from_http_not_readable(s3_private_bucket, test_data, mock_urlopen):
    mock_urlopen.return_value = FakeResponse(data=None, readable=False)
    r = Helper().download_from_http(body=test_data)
    assert r == 400

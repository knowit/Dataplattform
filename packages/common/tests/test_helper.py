from dataplattform.common.helper import save_document, empty_content_in_path
from unittest.mock import patch
from os import environ


def test_save_document():
    with patch('dataplattform.common.helper.launch_async_lambda') as launch_async_lambda:
        test_httpRequest = {'requestUrl': 'http://test_url.com'}
        save_document(test_httpRequest, filename='test.pdf', filetype='pdf')
        launch_async_lambda.assert_called_once()


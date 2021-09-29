from dataplattform.common.helper import save_document, empty_content_in_path
from unittest.mock import patch
from os import environ


def test_save_document():
    with patch('dataplattform.common.helper.launch_async_lambda') as launch_async_lambda:
        test_httpRequest = {'requestUrl': 'http://test_url.com'}
        save_document(test_httpRequest, filename='test.pdf', filetype='pdf')
        launch_async_lambda.assert_called_once()


def test_empty_content_in_path(s3_private_bucket):
    will_remain = [
        'private/remain/whatever.txt',
        'private/remain/whatever2.txt'
    ]
    will_be_deleted = [
        'private/deleted/whatever.txt',
        'private/deleted/whatever2.txt',
        'private/deleted/whatever3.txt',
        'private/deleted/whatever4.txt',
        'private/deleted/whatever5.txt',
        'private/deleted/whatever6.txt',
    ]
    for item in [*will_remain, *will_be_deleted]:
        s3_private_bucket.put_object(Body='some data', Key=item)

    len_remain_before = len(list(s3_private_bucket.objects.filter(Prefix='private/remain')))
    len_deleted_before = len(list(s3_private_bucket.objects.filter(Prefix='private/deleted')))
    empty_content_in_path(environ.get('PRIVATE_BUCKET'), "private/deleted")
    len_remain_after = len(list(s3_private_bucket.objects.filter(Prefix='private/remain')))
    len_deleted_after = len(list(s3_private_bucket.objects.filter(Prefix='private/deleted')))

    assert len_remain_before == len(will_remain)
    assert len_deleted_before == len(will_be_deleted)
    assert len_remain_after == len(will_remain)
    assert len_deleted_after == 0


def test_empty_content_in_path_with_filter(s3_private_bucket):
    will_remain = [
        'private/remain/whatever.txt',
        'private/remain/whatever2.txt',
        'private/remain/whatever3.txt',
        'private/remain/whatever4.txt',
        'private/remain/whatever5.txt',
        'private/remain/whatever6.txt',
    ]
    will_be_deleted = [
        'private/deleted/whatever2.txt',
    ]
    for item in [*will_remain, *will_be_deleted]:
        s3_private_bucket.put_object(Body='some data', Key=item)

    len_remain_before = len(list(s3_private_bucket.objects.filter(Prefix='private/remain')))
    len_deleted_before = len(list(s3_private_bucket.objects.filter(Prefix='private/deleted')))
    empty_content_in_path(environ.get('PRIVATE_BUCKET'), "private/deleted", filter_val='/whatever2.txt')
    len_remain_after = len(list(s3_private_bucket.objects.filter(Prefix='private/remain')))
    len_deleted_after = len(list(s3_private_bucket.objects.filter(Prefix='private/deleted')))

    assert len_remain_before == len(will_remain)
    assert len_deleted_before == len(will_be_deleted)
    assert len_remain_after == len(will_remain)
    assert len_deleted_after == 0

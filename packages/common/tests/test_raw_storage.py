from dataplattform.common.raw_storage import RawStorage
import re


def test_s3_private_put_data(s3_private_bucket):
    ext = 'txt'
    sub_path = 'test'
    rs = RawStorage()
    key = rs.write_to_private_bucket(data='some bytes', ext=ext, sub_path=sub_path)
    res = s3_private_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'
    assert re.fullmatch(r'private/test/[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}.txt', key)


def test_s3_public_put_data(s3_public_bucket):
    ext = 'txt'
    sub_path = 'test'
    rs = RawStorage()
    key = rs.write_to_public_bucket('some bytes', ext=ext, sub_path=sub_path)
    res = s3_public_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'
    assert re.fullmatch(r'public/test/[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}.txt', key)

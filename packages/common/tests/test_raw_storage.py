from dataplattform.common import raw_storage as rs


def test_s3_private_put_data(s3_private_bucket):
    key = rs.write_to_private_bucket('some bytes', '.txt')
    res = s3_private_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'
    assert 'private/' in key


def test_s3_public_put_data(s3_public_bucket):
    key = rs.write_to_public_bucket('some bytes', '.txt')
    res = s3_public_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'

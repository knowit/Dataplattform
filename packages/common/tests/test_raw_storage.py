from dataplattform.common.raw_storage import write_file_to_bucket


def test_s3_public_put_data(s3_public_bucket):
    filename = 'public/whatever.txt'
    key = write_file_to_bucket('some bytes', filename=filename)
    res = s3_public_bucket.Object(key).get()['Body'].read().decode('utf-8')
    assert res == 'some bytes'
    assert filename == key

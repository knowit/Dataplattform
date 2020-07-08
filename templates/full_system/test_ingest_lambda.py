from ingest_lambda import handler
from json import loads


def test_initial_ingest(s3_bucket, sqs_queue):
    handler(None, None)
    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data is not None

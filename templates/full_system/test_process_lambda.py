from process_lambda import handler


def test_initial_process():
    event = {
        "Records": [{
            "messageId": "717af8fb-3314-4c21-a025-936b71a0fe53",
            "receiptHandle": "gdergfsdvsdfwef",
            "body": "1593430009",
            "attributes": {
                "ApproximateReceiveCount": "18",
                "SentTimestamp": "1593430009419",
                "SequenceNumber": "18854662156120818432",
                "MessageGroupId": "messageGroup1",
                "SenderId": "dev-test-lambda-ingest",
                "MessageDeduplicationId": "adadewd",
                "ApproximateFirstReceiveTimestamp": "1593430015749",
            },
            "messageAttributes": {
                "s3FileName": "some-s3-file-key"
            },
            "md5OfBody": "asdawsdv",
            "eventSource": "aws:sqs",
            "eventSourceARN": "asdwda:dev-sqs-test.fifo",
            "awsRegion": "eu-central-1",
        }]
    }
    handler(event, None)
    assert True

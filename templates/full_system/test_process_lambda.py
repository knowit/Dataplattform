from process_lambda import handler


def test_initial_process():
    event = {
        "Records": [
            {
                "messageId": "fd514109-01fc-4163-a7a3-25d17d2023a9",
                "receiptHandle": "AQEBdh91+VKw7+oBOsmWCM5UeZ4EfydJ4MFHYledjYRYp4kRbONgLGhcY3XShzf1upbGeV+Q5y0FQXp1hUFcxFqf9dk7TQnsQHKMpphGPIaC/dpkNU4GCR/t7ZApTJPzwFbwu5QjRKCXxjEyj+f+ZIf7mEpkThupbZv+g/Ne/QK04GwO0oIA23YQaMYoWTwoqJMLi3YGLJEUliOE7M2ERLDSilska91GeitvAUZzJM1ZncJqfHLmBfK7z5tM6cBCdhlqT1j0zX8E7R/L7xh/mqWY9cHtQsDpsGIfbQuXmsV2kaw=",
                "body": "data/level-1/sqs_integration_data_folder/raw/1593536878.json",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1593536878685",
                    "SequenceNumber": "18854689514652912640",
                    "MessageGroupId": "dev-sqs-test.fifo-group1",
                    "SenderId": "AROAVC5W4ROCIZEETHSGZ:dev-test-lambda-ingest",
                    "MessageDeduplicationId": "9b8f514c7203c63993112ce50fa7564a0c80784797aa9d76707f21e5c24a4d6d",
                    "ApproximateFirstReceiveTimestamp": "1593536878685",
                },
                "messageAttributes": {
                    "s3FileName": {
                        "stringValue": "data/level-1/sqs_integration_data_folder/raw/1593536878.json",
                        "stringListValues": [],
                        "binaryListValues": [],
                        "dataType": "String",
                    }
                },
                "md5OfBody": "d57f5fee12763243294637ded885d324",
                "md5OfMessageAttributes": "fa4ea0edcb82844500129c8fed568092",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:eu-central-1:349886516100:dev-sqs-test.fifo",
                "awsRegion": "eu-central-1",
            }
        ]
    }

    handler(event, None)
    assert True

from process_lambda import handler
from pytest import fixture
from json import loads, load
from responses import RequestsMock, GET
import pandas as pd
from os import path


if __name__ == '__main__':
    event = {
        "Records": [{
            "messageId": "717af8fb-3314-4c21-a025-936b71a0fe53",
            "receiptHandle": "AQEBuxroghZ5xZlz/6BcAXXzRpondZD5jYujkJanV0JOYm7r4VO6KYtqVW17W6NUkyuEBC3tis0FFRC3Xp65NaIji0qXhZPky2PYi/o05pPUuZSNla8+NDlTJNWLeR0zCEb0u7L2zFZqb53nQ/o/M3kJyBFxLFlgaiAvAW9hPwGaUfBmPI7LCZOE70IzBnB0gKCqYt7m2tbzJGSsvzeNwFgpmvndJaDVMuO/8kQmvm49JEiatxbsqHlMZBXSB9nl3rSXb8/NMlaGXG7eLFou7owbNeEss+bZpcSC6XplPkVfNFk=",
            "body": "1593430009",
            "attributes": {
                "ApproximateReceiveCount": "18",
                "SentTimestamp": "1593430009419",
                "SequenceNumber": "18854662156120818432",
                "MessageGroupId": "messageGroup1",
                "SenderId": "AROAVC5W4ROCO7HXUJVWS:dev-test-lambda-ingest",
                "MessageDeduplicationId": "b9e5577ce0a2147720f12900eca1405db403b4b7b2e8b3cf41efad3615bb8ac1",
                "ApproximateFirstReceiveTimestamp": "1593430015749",
            },
            "messageAttributes": {},
            "md5OfBody": "c00c61675d00ab1dac4584e526b7cb44",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:eu-central-1:349886516100:dev-sqs-test.fifo",
            "awsRegion": "eu-central-1",
        }]
    }
    handler(event, event)

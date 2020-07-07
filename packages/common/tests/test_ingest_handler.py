from dataplattform.common import schema
from dataplattform.common.handlers import ingest as handler
import re
import pytest


def test_empty_handler():
    ingest_handler = handler.IngestHandler()

    with pytest.raises(AssertionError):
        ingest_handler(None)


def test_handler_response():
    ingest_handler = handler.IngestHandler()

    @ingest_handler.ingest()
    def test(event):
        return handler.Response(body='hello test')

    res = ingest_handler(None)
    assert res['body'] == 'hello test'


def test_handler_data(s3_bucket):
    ingest_handler = handler.IngestHandler()

    @ingest_handler.ingest()
    def test(event):
        return schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='hello test'
        )

    ingest_handler(None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = schema.Data.from_json(response['Body'].read())
    assert data.data == 'hello test'


def test_handler_validate(mocker):
    ingest_handler = handler.IngestHandler()

    @ingest_handler.validate()
    def test_validate(event):
        return False

    res = ingest_handler(None)
    assert res['statusCode'] == 403


def test_handler_invalid_skip_ingest(mocker):
    ingest_handler = handler.IngestHandler()

    @ingest_handler.validate()
    def test_validate(event):
        return False

    ingest_handler.wrapped_func['ingest'] = mocker.stub()

    ingest_handler(None)

    ingest_handler.wrapped_func['ingest'].assert_not_called()


def test_handler_valid_call_ingest(mocker):
    ingest_handler = handler.IngestHandler()

    @ingest_handler.validate()
    def test_validate(event):
        return True

    ingest_handler.wrapped_func['ingest'] = mocker.MagicMock(return_value=handler.Response())

    ingest_handler(None)

    ingest_handler.wrapped_func['ingest'].assert_called_once()


def test_handler_sqs_event(sqs_queue):
    ingest_handler = handler.IngestHandler()

    @ingest_handler.ingest()
    def test(event):
        return schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data='hello test'
        )

    ingest_handler(None)

    message = next(iter(sqs_queue.receive_messages()))

    assert re.fullmatch(r'data/test/raw/[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}.json', message.body)
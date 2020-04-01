from dataplattform.common import handler
from dataplattform.common import schema


def test_empty_ingestion_handler():
    ingest_handler = handler.ingestion()
    res = ingest_handler(None)

    assert res['statusCode'] == 200 and res['body'] == ''


def test_ingestion_handler_response():
    ingest_handler = handler.ingestion()

    @ingest_handler.ingest()
    def test(event):
        return handler.Response(body='hello test')

    res = ingest_handler(None)
    assert res['body'] == 'hello test'


def test_ingestion_handler_data(s3_bucket):
    ingest_handler = handler.ingestion()

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


def test_ingestion_handler_validate(mocker):
    ingest_handler = handler.ingestion()

    @ingest_handler.validate()
    def test_validate(event):
        return False

    res = ingest_handler(None)
    assert res['statusCode'] == 403


def test_ingestion_handler_invalid_skip_ingest(mocker):
    ingest_handler = handler.ingestion()

    @ingest_handler.validate()
    def test_validate(event):
        return False

    ingest_handler.ingest_func = mocker.stub()

    ingest_handler(None)

    ingest_handler.ingest_func.assert_not_called()


def test_ingestion_handler_valid_call_ingest(mocker):
    ingest_handler = handler.ingestion()

    @ingest_handler.validate()
    def test_validate(event):
        return True

    ingest_handler.ingest_func = mocker.MagicMock(return_value=handler.Response())

    ingest_handler(None)

    ingest_handler.ingest_func.assert_called_once()

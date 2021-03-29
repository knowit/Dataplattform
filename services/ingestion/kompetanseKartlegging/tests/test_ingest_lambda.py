from services.ingestion.kompetanseKartlegging.kompetansekartlegging_ingest_lambda import handler


def test_response():
    data = handler(None)
    assert data is not None

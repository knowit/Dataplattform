from my_ingest_service import handler


def test_pass():
    handler(None)
    assert True

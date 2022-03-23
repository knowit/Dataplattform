from yrweather.yr_ingest_lambda import handler
from pytest import fixture
from responses import RequestsMock, GET
from json import loads
from os import path

location = 'Norway/Oslo/Oslo/Lakkegata'
url = f'https://www.yr.no/place/{location}/varsel_time_for_time.xml'


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.xml'), 'r') as f:
        yield f.read()


@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs


def test_handler_data_in_s3(s3_bucket, mocked_responses, test_data):
    mocked_responses.add(GET, url, body=test_data, status=200)

    handler(None, None)

    s3_object_summary = next(iter(s3_bucket.objects.all()), None)
    assert s3_object_summary is not None


def test_handler_data_length(s3_bucket, mocked_responses, test_data):
    mocked_responses.add(GET, url, body=test_data, status=200)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert len(data['data']) == 24


def test_handler_data(s3_bucket, mocked_responses, test_data):
    mocked_responses.add(GET, url, body=test_data, status=200)

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    expected = {
        'location': 'Norway/Oslo/Oslo/Lakkegata',
        'location_name': 'Lakkegata',
        'precipitation': 0.0,
        'wind_speed': 4.9,
        'temperature': 9,
        'air_pressure': 997.0
    }

    assert all([data['data'][0][k] == v for k, v in expected.items()])

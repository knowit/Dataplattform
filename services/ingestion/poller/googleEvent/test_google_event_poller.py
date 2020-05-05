from google_event_poller import handler
from pytest import fixture
from json import loads
from datetime import datetime


@fixture
def events_list_mock(mocker):
    mock_service_builder = mocker.patch('google_event_poller.googleapiclient.discovery.build')
    mocker.patch('google_event_poller.ServiceAccountCredentials')

    service_mock = mocker.MagicMock()
    events_mock = mocker.MagicMock()
    events_list_mock = mocker.MagicMock()

    events_mock.list.return_value = events_list_mock
    service_mock.events.return_value = events_mock
    mock_service_builder.return_value = service_mock

    yield events_list_mock


def test_handler_write(s3_bucket, events_list_mock):

    events_list_mock.execute.return_value = {
        'items': [{
            'id': '1234',
            'start': {
                'dateTime': datetime.utcnow().isoformat()
            },
            'end': {
                'dateTime': datetime.utcnow().isoformat()
            },
            'location': 'Enheter-box1'
         },
         {
            'id': '1235',
            'start': {
                'dateTime': datetime.utcnow().isoformat()
            },
            'end': {
                'dateTime': datetime.utcnow().isoformat()
            }
        }]
    }

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert len(data['data']) == 2
    assert 'event_id' in data['data'][0] and data['data'][0]['event_id'] == '1234'


def test_handler_write_time_formats(s3_bucket, events_list_mock):
    events_list_mock.execute.return_value = {
        'items': [{
            'id': '1234',
            'start': {
            },
            'location': 'Enheter-box1'
         },
         {
            'id': '1235',
            'start': {
                'dateTime': datetime.utcnow().isoformat()
            },
            'end': {
                'date': "2020-05-05"
            }
        }]
    }

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert True


def test_handler_data_content(s3_bucket, events_list_mock):
    events_list_mock.execute.return_value = {
        'items': [{
            'id': '1234',
            'start': {
                'dateTime': datetime.utcnow().isoformat()
            },
            'end': {
                'dateTime': datetime.utcnow().isoformat()
            }
        }]
    }

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert '1234' in data['data']


def test_event_sync(s3_bucket, events_list_mock):
    assert True

# TODO:

# Test pagination 
# Test synk med mock? Hvordan
# Test pagiation med mock (se stash)
# Test error codes (404 etc.)
# Test different time/date formats
# Test input error handling in read from events


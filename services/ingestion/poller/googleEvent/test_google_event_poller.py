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
            }
        }]
    }

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert '1234' in data['data']

from google_event_poller import handler
from pytest import fixture
from json import loads
from datetime import datetime
import copy


@fixture
def events_list_mock(mocker):
    mock_service_builder = mocker.patch('google_event_poller.googleapiclient.discovery.build')
    mocker.patch('google_event_poller.ServiceAccountCredentials')

    service_mock = mocker.MagicMock()
    events_mock = mocker.MagicMock()
    events_list_mock_page_1 = mocker.MagicMock()
    events_list_mock_page_2 = mocker.MagicMock()

    events_mock.list.return_value = events_list_mock_page_1
    events_mock.list_next.return_value = events_list_mock_page_2

    service_mock.events.return_value = events_mock
    mock_service_builder.return_value = service_mock

    def set_payload(payload, next_page_payload):
        events_list_mock_page_1.execute.return_value = {**payload, **{'nextPageToken': 'test_page_token'}}
        events_list_mock_page_2.execute.return_value = {**next_page_payload,
                                                        **{'nextSyncToken': 'test_sync_token'}}
    yield set_payload


@fixture
def events_list_mock_mult_calendars(mocker):
    mock_service_builder = mocker.patch('google_event_poller.googleapiclient.discovery.build')
    mocker.patch('google_event_poller.ServiceAccountCredentials')

    service_mock = mocker.MagicMock()
    events_mock = mocker.MagicMock()

    mock_service_builder.builder.return_value = service_mock

    service_mock.events.return_value = events_mock
    mock_service_builder.return_value = service_mock

    def payload(data):
        def list_side_effect(**params):
            events_list_mock = mocker.MagicMock()
            events_list_mock.execute.return_value = {**data, **{'syncToken': '123', 'calenderId': params['calendarId']}}
            return events_list_mock

        events_mock.list = mocker.MagicMock(
            side_effect=list_side_effect)
    yield payload


def test_events_multiple_calendars(s3_bucket, events_list_mock_mult_calendars):
    events_list_mock_mult_calendars({
        'items':
        [{
            'id': '1234',
            'start': {
                'dateTime': ''
            },
            'end': {
                'dateTime': ''
            },
            'location': 'Enheter-box1'
            },
            {
            'id': '1235',
            'start': {
                'dateTime': ''
            },
            'end': {
                'dateTime': ''
            }
        }]
    })

    expected = [{'event_id': '1234',
                 'calendar_id': '1',
                 'timestamp_from': '',
                 'timestamp_to': '',
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 },
                {'event_id': '1235',
                 'calendar_id': '1',
                 'timestamp_from': '',
                 'timestamp_to': '',
                 'event_summary': '',
                 'event_button_names': [],
                 'creator': ''
                }]
    expected2 = copy.deepcopy(expected)
    expected2[0]['calendar_id'] = '2'
    expected2[1]['calendar_id'] = '2'
    handler(None, None)
    expected_new = [expected[0], expected[1], expected2[0], expected2[1]]
    
    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert [i for i in data['data'] if i not in expected_new] == []


def test_events_pagination(s3_bucket, events_list_mock):
    items1 = {
        'items': [{
            'id': '1234',
            'start': {
                'dateTime': ''
            },
            'end': {
                'dateTime': ''
            },
            'location': 'Enheter-box1'
            }]}
    items2 = {
        'items': [{
            'id': '1235',
            'start': {
                'dateTime': ''
            },
            'end': {
                'dateTime': ''
            },
            'location': ''
            }]}

    events_list_mock(items1, items2)

    expected = [{'event_id': '1234',
                 'calendar_id': '1',
                 'timestamp_from': '',
                 'timestamp_to': '',
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 },
                {'event_id': '1235',
                 'calendar_id': '1',
                 'timestamp_from': '',
                 'timestamp_to': '',
                 'event_summary': '',
                 'event_button_names': [],
                 'creator': ''
                 }]
    expected2 = copy.deepcopy(expected)
    expected2[0]['calendar_id'] = '2'
    expected2[1]['calendar_id'] = '2'
    handler(None, None)
    expected_new = [expected[0], expected[1], expected2[0], expected2[1]]

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert [i for i in data['data'] if i not in expected_new] == []



def test_handler_write(s3_bucket, events_list_mock):
    events_list_mock({
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
    }, {})

    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert '1234' in data['data'][0]['event_id'] and '1235' in data['data'][1]['event_id']



# TODO:
# Test time formats
# Test error handling
# Filter future events 

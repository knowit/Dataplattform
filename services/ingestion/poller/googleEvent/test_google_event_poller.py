from google_event_poller import handler
from pytest import fixture
from json import loads
from datetime import datetime
from botocore.exceptions import ClientError
import copy
from time import sleep


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

    def payload():
        def list_side_effect(**params):
            def generate_cal_events(calendar_id):
                start_time = datetime(2019, 6, 15+int(calendar_id) - 1, 18, 30)
                end_time = datetime(2019, 6, 15+int(calendar_id) - 1, 19, 30)
                test_events = {'items': [{
                    'id': str(1234 + int(calendar_id)),
                    'start': {
                        'dateTime': start_time.isoformat()
                                },
                    'end': {
                        'dateTime': end_time.isoformat()
                            },
                    'location': 'Enheter-box' + calendar_id
                    }]}
                return test_events
            events_list_mock = mocker.MagicMock()
            events_list_mock.execute.return_value = {**generate_cal_events(params['calendarId']),
                                                     **{'calendarId': params['calendarId']}}
            return events_list_mock
        events_mock.list = mocker.MagicMock(
            side_effect=list_side_effect)

    yield payload


def test_events_multiple_calendars(s3_bucket, events_list_mock_mult_calendars):
    start_time_1 = int(datetime(2019, 6, 15, 18, 30).timestamp())
    end_time_1 = int(datetime(2019, 6, 15, 19, 30).timestamp())

    start_time_2 = int(datetime(2019, 6, 16, 18, 30).timestamp())
    end_time_2 = int(datetime(2019, 6, 16, 19, 30).timestamp())

    events_list_mock_mult_calendars()
    expected = [{'event_id': '1235',
                 'calendar_id': '1',
                 'timestamp_from': start_time_1,
                 'timestamp_to': end_time_1,
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 }]
    expected2 = [{'event_id': '1236',
                  'calendar_id': '2',
                  'timestamp_from': start_time_2,
                  'timestamp_to': end_time_2,
                  'event_summary': '',
                  'event_button_names': ['box2'],
                  'creator': ''
                }]
    handler(None, None)

    expected_new = [expected[0], expected2[0]]
    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert [i for i in data['data'] if i not in expected_new] == []


def test_events_pagination(s3_bucket, events_list_mock):
    start_time_1 = datetime(2019, 6, 15, 18, 30)
    end_time_1 = datetime(2019, 6, 15, 19, 30)

    items1 = {
        'items': [{
            'id': '1234',
            'start': {
                'dateTime': start_time_1.isoformat()
            },
            'end': {
                'dateTime': end_time_1.isoformat()
            },
            'location': 'Enheter-box1'
            }]}
    items2 = {
        'items': [{
            'id': '1235',
            'start': {
                'dateTime': start_time_1.isoformat()
            },
            'end': {
                'dateTime': end_time_1.isoformat()
            },
            'location': ''
            }]}

    events_list_mock(items1, items2)

    expected = [{'event_id': '1234',
                 'calendar_id': '1',
                 'timestamp_from': int(start_time_1.timestamp()),
                 'timestamp_to': int(end_time_1.timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 },
                {'event_id': '1235',
                 'calendar_id': '1',
                 'timestamp_from': int(start_time_1.timestamp()),
                 'timestamp_to': int(end_time_1.timestamp()),
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


def test_handler_time_format(s3_bucket, events_list_mock):
    test_date = datetime(2014, 4, 3).date()
    test_date2 = datetime(2014, 4, 4).date()
    test_date_str = test_date.isoformat()
    test_date2_str = test_date2.isoformat()

    events_list_mock({
        'items': [{
            'id': '1234',
            'start': {
                'date': test_date_str
            },
            'end': {
                'date': test_date2_str
            },
            'location': 'Enheter-box1'
        }]},
        {})

    handler(None, None)

    expected = [{'event_id': '1234',
                 'calendar_id': '1',
                 'timestamp_from': int(datetime(test_date.year, test_date.month, test_date.day).timestamp()),
                 'timestamp_to': int(datetime(test_date2.year, test_date2.month, test_date2.day).timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 },
                {'event_id': '1234',
                 'calendar_id': '2',
                 'timestamp_from': int(datetime(test_date.year, test_date.month, test_date.day).timestamp()),
                 'timestamp_to': int(datetime(test_date2.year, test_date2.month, test_date2.day).timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 }]

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert [i for i in data['data'] if i not in expected] == []


def test_handler_time_format_timezone(s3_bucket, events_list_mock):
    start_time_1 = datetime(2019, 6, 15, 4, 0)  # GMT - 5
    start_time_oslo_time = datetime(2019, 6, 15, 10, 0)
    end_time_1 = datetime(2019, 6, 15, 13, 30)  # GMT + 2

    events_list_mock({
        'items': [{
            'id': '1234',
            'start': {
                'dateTime': start_time_1.isoformat(),
                'timeZone': 'US/Eastern',
            },
            'end': {
                'dateTime': end_time_1.isoformat(),
                'timeZone': 'Europe/Oslo'
            },
            'location': 'Enheter-box1'
        }]},
        {})

    handler(None, None)

    expected = [{'event_id': '1234',
                 'calendar_id': '1',
                 'timestamp_from': int(start_time_oslo_time.timestamp()),
                 'timestamp_to': int(end_time_1.timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 },
                {'event_id': '1234',
                 'calendar_id': '2',
                 'timestamp_from': int(start_time_oslo_time.timestamp()),
                 'timestamp_to': int(end_time_1.timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 }]

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert [i for i in data['data'] if i not in expected] == []


def test_handler_set_and_get_from_ssm(events_list_mock, ssm_client):
    events_list_mock({}, {})

    expectionRaised = False
    try:
        last_sync_time_for_cal1 = ssm_client.get_parameter(Name='/dev/testService/last_sync_time_1',
                                                           WithDecryption=False)['Parameter']['Value']
    except ClientError as e:
        expectionRaised = True
        assert (e.response['Error']['Code'] == 'ParameterNotFound')

    handler(None, None)

    last_sync_time_for_cal1 = ssm_client.get_parameter(Name='/dev/testService/last_sync_time_1',
                                                       WithDecryption=False)['Parameter']['Value']

    sleep(10)
    handler(None, None)

    new_sync_time_for_cal1 = ssm_client.get_parameter(Name='/dev/testService/last_sync_time_1',
                                                      WithDecryption=False)['Parameter']['Value']

    sync_time_is_updated = new_sync_time_for_cal1 != last_sync_time_for_cal1

    assert last_sync_time_for_cal1 is not None and expectionRaised and sync_time_is_updated

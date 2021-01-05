import pytest
import app
import json


@pytest.fixture
def client():
    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        yield client


def test_delete_report(client, dynamo_mock):
    response = client.delete('/data/report/testReport')
    items = dynamo_mock.scan()['Items']
    assert response.status_code == 204
    assert all(item['name'] != 'testReport' for item in items)


def test_delete_report_publish_event(client, dynamo_mock, sns_topic, sqs_queue):
    sns_topic.subscribe(
        Protocol='sqs',
        Endpoint=sqs_queue.attributes['QueueArn'])
    response = client.delete('data/report/testReport')
    message = json.loads(json.loads(next(iter(sqs_queue.receive_messages())).body)['Message'])

    assert response.status_code == 204
    assert message['name'] == 'testReport'
    assert message['dataProtection'] == 3


def test_delete_report_not_found(client, dynamo_mock):
    response = client.delete('data/report/fakeReport')
    assert response.status_code == 404

from jira_webhook import handler
from dataplattform.testing.events import APIGateway
from json import dumps, loads
import pandas as pd


def test_invalid():
    res = handler(APIGateway().to_dict())

    assert res['statusCode'] == 403


def test_valid():
    res = handler(APIGateway(
        path_parameters={
            'secret': 'iamsecret'
        },
        body=dumps({
            'webhookEvent': 'jira:issue_created',
            'issue': {
                'key': 'TEST-1234',
                'fields': {
                    'created': '2020-01-01T00:00:00.000-0000',
                    'updated': '2020-01-01T00:00:00.000-0000',
                    'status': {'name': 'Open'},
                    'labels': ['Test Testerson'],
                }
            }
        })
    ).to_dict())

    assert res['statusCode'] == 200


def test_insert_data(s3_bucket):
    handler(APIGateway(
        path_parameters={
            'secret': 'iamsecret'
        },
        body=dumps({
            'webhookEvent': 'jira:issue_created',
            'issue': {
                'key': 'TEST-1234',
                'fields': {
                    'created': '2020-01-01T00:00:00.000-0000',
                    'updated': '2020-01-01T00:00:00.000-0000',
                    'status': {'name': 'Open'},
                    'labels': ['Test Testerson'],
                }
            }
        })
    ).to_dict())

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['data']['issue'] == 'TEST-1234' and\
        data['data']['customer'] == 'Test Testerson' and\
        data['data']['issue_status'] == 'Open'


def test_handler_process(s3_bucket, create_table_mock):
    handler(APIGateway(
        path_parameters={
            'secret': 'iamsecret'
        },
        body=dumps({
            'webhookEvent': 'jira:issue_created',
            'issue': {
                'key': 'TEST-1234',
                'fields': {
                    'created': '2020-01-01T00:00:00.000-0000',
                    'updated': '2020-01-01T00:00:00.000-0000',
                    'status': {'name': 'Open'},
                    'labels': ['Test Testerson'],
                }
            }
        })
    ).to_dict())

    create_table_mock.assert_table_data_column(
        'jira_issue_created',
        'issue_status',
        pd.Series(['Open']))

    create_table_mock.assert_table_data_column(
        'jira_issue_created',
        'customer',
        pd.Series(['Test Testerson']))

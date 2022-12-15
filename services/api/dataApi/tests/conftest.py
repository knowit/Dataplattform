from os import environ
import pytest
import datetime

import boto3
from botocore.exceptions import ClientError
from moto import mock_dynamodb2


@pytest.fixture
def glue_test_data():
    d = datetime.datetime(2015, 1, 1).isoformat()

    yield {
        'databases': {
            'test_database': {
                'Name': 'test_database',
                'CreateTime': d,
            },
            'default': {
                'Name': 'default',
                'CreateTime': d,
            }
        },
        'tables': {
            'test_database': {
                'test_table': {
                    'Name': 'test_table',
                    'DatabaseName': 'test_database',
                    'CreateTime': d,
                    'UpdateTime': d,
                    'LastAccessTime': d,
                    'StorageDescriptor': {
                        'Columns': [{
                            'Name': 'col1',
                            'Type': 'string',
                        }]
                    },
                    'PartitionKeys': []
                },
                'test_table_no_update': {
                    'Name': 'test_table_no_update',
                    'DatabaseName': 'test_database',
                    'CreateTime': d,
                    'StorageDescriptor': {
                        'Columns': [{
                            'Name': 'col1',
                            'Type': 'string',
                        }]
                    },
                    'PartitionKeys': []
                }
            }
        },
        'errors': {
            'not_found': {
                'Error': {
                    'Code': 'EntityNotFoundException',
                    'Message': ''
                },
                'ResponseMetadata': {
                    'HTTPStatusCode': 404
                }
            },
            'forbidden': {
                'Error': {
                    'Code': 'AccessDeniedException',
                    'Message': 'secret message'
                },
                'ResponseMetadata': {
                    'HTTPStatusCode': 403
                }
            }
        }
    }


@pytest.fixture(autouse=True)
def mocked_glue_services(mocker, glue_test_data):
    glue_mock = mocker.MagicMock()

    def raise_(ex):
        raise ex

    def error_type(name):
        return 'forbidden' if 'forbidden' in name else 'not_found'

    glue_mock.get_databases = mocker.MagicMock(
        return_value={
            'DatabaseList': glue_test_data['databases'].values(),
        })

    glue_mock.get_database = mocker.MagicMock(
        side_effect=lambda **kwargs: {
            'Database': glue_test_data['databases'][kwargs['Name']]
        }
        if kwargs['Name'] in glue_test_data['databases']
        else raise_(ClientError(glue_test_data['errors'][error_type(kwargs['Name'])], 'get_database')))

    glue_mock.get_tables = mocker.MagicMock(
        side_effect=lambda **kwargs: {
            'TableList': glue_test_data['tables'][kwargs['DatabaseName']].values()
        }
        if kwargs['DatabaseName'] in glue_test_data['tables']
        else raise_(ClientError(glue_test_data['errors'][error_type(kwargs['Name'])], 'get_tables')))

    glue_mock.get_table = mocker.MagicMock(
        side_effect=lambda **kwargs: {
            'Table': glue_test_data['tables'][kwargs['DatabaseName']][kwargs['Name']]
        }
        if kwargs['DatabaseName'] in glue_test_data['tables'] and
        kwargs['Name'] in glue_test_data['tables'][kwargs['DatabaseName']]
        else raise_(ClientError(glue_test_data['errors'][error_type(kwargs['Name'])], 'get_table')))

    def mock_paginator_side_effect(service):
        def mock_generator(**kwargs):
            yield getattr(glue_mock, service)(**kwargs)

        paginator_mock = mocker.MagicMock()
        paginator_mock.paginate = mocker.MagicMock(
            side_effect=mock_generator
        )
        return paginator_mock

    glue_mock.get_paginator = mocker.MagicMock(
        side_effect=mock_paginator_side_effect
    )
    yield glue_mock


@pytest.fixture(autouse=True)
def mocked_athena_services(mocker):
    athena_mock = mocker.MagicMock()

    athena_mock.get_query_execution = mocker.MagicMock(
        return_value={
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'},
                'ResultConfiguration': {'OutputLocation': 's3://testlake/query/mock.csv'}
            }
        })
    yield athena_mock


@pytest.fixture(autouse=True)
def mock_services(mocker, mocked_glue_services, mocked_athena_services):
    def find_service(service):
        if service == "glue":
            return mocked_glue_services
        elif service == "athena":
            return mocked_athena_services
        else:
            return mocker.DEFAULT

    mocker.patch(
        "boto3.client",
        side_effect=find_service
    )


@pytest.fixture(autouse=True)
def setup_mock_athena_result(s3_bucket):
    mock_data = '"col0","col1"\n"row0",0\n"row1",1'
    s3_bucket.Object('query/mock.csv').put(Body=mock_data.encode('utf-8'))


@pytest.fixture
def db_data():
    yield [
        {
            "created": "2020-10-14T10:32:23.971390",
            "dataProtection": 3,
            "lastCacheUpdate": "2020-10-14T10:32:23.971390",
            "lastUsed": None,
            "name": "testReport",
            "queryString": "COUNT(*) from dev_level_3_database.cv_partner_employees",
            "tables": [
                "test_table1",
                "test_table2"
            ]
        },
        {
            "created": "2020-10-14T10:32:23.971390",
            "dataProtection": 3,
            "lastCacheUpdate": "2020-10-14T10:32:23.971390",
            "lastUsed": None,
            "name": "anotherReport",
            "queryString": "COUNT(*) from dev_level_3_database.cv_partner_employees",
            "tables": [
                "test_table3",
                "test_table4"
            ]
        }

    ]


@pytest.fixture
def dynamo_mock(db_data):
    with mock_dynamodb2():
        db = boto3.resource('dynamodb')
        table = db.create_table(
            AttributeDefinitions=[{'AttributeName': "name", 'AttributeType': 'S'}],
            TableName=f'{environ.get("STAGE", "dev")}_reports_table',
            KeySchema=[{'AttributeName': "name", 'KeyType': 'HASH'}],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )
        for item in db_data:
            table.put_item(
                Item=item,
                Expected={
                    'name': {'Exists': False}
                }
            )
        yield table

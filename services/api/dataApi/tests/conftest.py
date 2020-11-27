import pytest
import datetime
from botocore.exceptions import ClientError


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
                }
            }
        }
    }


@pytest.fixture(autouse=True)
def mocked_glue_services(mocker, glue_test_data):
    glue_mock = mocker.MagicMock()

    def raise_(ex):
        raise ex

    glue_mock.get_databases = mocker.MagicMock(
        return_value={
            'DatabaseList': glue_test_data['databases'].values(),
        })

    glue_mock.get_database = mocker.MagicMock(
        side_effect=lambda **kwargs: {
            'Database': glue_test_data['databases'][kwargs['Name']]
        }
        if kwargs['Name'] in glue_test_data['databases']
        else raise_(ClientError(glue_test_data['errors']['not_found'], 'get_database')))

    glue_mock.get_tables = mocker.MagicMock(
        side_effect=lambda **kwargs: {
            'TableList': glue_test_data['tables'][kwargs['DatabaseName']].values()
        }
        if kwargs['DatabaseName'] in glue_test_data['tables']
        else raise_(ClientError(glue_test_data['errors']['not_found'], 'get_tables')))

    glue_mock.get_table = mocker.MagicMock(
        side_effect=lambda **kwargs: {
            'Table': glue_test_data['tables'][kwargs['DatabaseName']][kwargs['Name']]
        }
        if kwargs['DatabaseName'] in glue_test_data['tables'] and
        kwargs['Name'] in glue_test_data['tables'][kwargs['DatabaseName']]
        else raise_(ClientError(glue_test_data['errors']['not_found'], 'get_table')))

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

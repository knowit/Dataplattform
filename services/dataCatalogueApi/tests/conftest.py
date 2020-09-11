import pytest
import boto3
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

    mocker.patch(
        'boto3.client',
        side_effect=lambda service: glue_mock if service == 'glue' else boto3.client(service))

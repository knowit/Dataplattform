import pytest
import re
from os import environ
from unittest.mock import call
from delete_old_guid_partitions import get_guids, check_partitionkeys, transform_uri, handler
from dataplattform.common.repositories.person_repository import PersonRepository


def get_glue_data():
    bucket = environ.get('DATALAKE')
    return {
        'databases': [
            {
                'Name': 'test-database-1',
                'Description': 'The first test database'
            },
            {
                'Name': 'test-database-2',
                'Description': 'The second test database'
            }
        ],
        'tables': [
            {
                'Name': 'partitioned-table-1',
                'DatabaseName': 'test-database-1',
                'Description': "Partitioned table in the first test database",
                'PartitionKeys': [
                    {
                        'Name': 'guid',
                        'Type': 'STRING'
                    },
                    {
                        'Name': 'month',
                        'Type': 'INT'
                    }
                ]
            },
            {
                'Name': 'table-1',
                'DatabaseName': 'test-database-1',
                'Description': "Non-partitioned table in the first test database",
                'PartitionKeys': []

            },
            {
                'Name': 'partitioned-table-2',
                'DatabaseName': 'test-database-2',
                'Description': "Partitioned table in the second test database",
                'PartitionKeys': [
                    {
                        'Name': 'guid',
                        'Type': 'STRING'
                    },
                    {
                        'Name': 'default_branch',
                        'Type': 'STRING'
                    }
                ]
            },
            {
                'Name': 'table-2',
                'DatabaseName': 'test-database-2',
                'Description': "Non-partitioned table in the second test database",
                'PartitionKeys': []

            }
        ],
        'partitions': [
            {
                'Values': [
                    'some-guid-12345',
                    12
                ],
                'DatabaseName': 'test-database-1',
                'TableName': 'partitioned-table-1',
                'StorageDescriptor': {
                    'Location': f's3://{bucket}/path/partitioned-table-1/guid=some-guid-12345/month=12/'
                }
            },
            {
                'Values': [
                    'another-guid-12345',
                    12
                ],
                'DatabaseName': 'test-database-1',
                'TableName': 'partitioned-table-1',
                'StorageDescriptor': {
                    'Location': f's3://{bucket}/path/partitioned-table-1/guid=another-guid-12345/month=12/'
                }
            },
            {
                'Values': [
                    'some-guid-12345',
                    'dev'
                ],
                'DatabaseName': 'test-database-2',
                'TableName': 'partitioned-table-2',
                'StorageDescriptor': {
                    'Location': f's3://{bucket}/path/partitioned-table-2/guid=some-guid-12345/default_branch=dev/'
                }
            },
            {
                'Values': [
                    'another-guid-12345',
                    'main'
                ],
                'DatabaseName': 'test-database-2',
                'TableName': 'partitioned-table-2',
                'StorageDescriptor': {
                    'Location': f's3://{bucket}/path/partitioned-table-2/guid=another-guid-12345/default_branch=main/'
                }
            },
        ]
    }


@pytest.fixture()
def s3(s3_bucket):
    keys = [
        'path/table1/file1.file',
        'path/table1/file2.file',
        'path/table1/file3.file',
        'path/table2/file1.file',
        'path/partitioned-table-1/guid=some-guid-12345/month=12/file1.file',
        'path/partitioned-table-1/guid=another-guid-12345/month=12/file1.file',
        'path/partitioned-table-2/guid=some-guid-12345/default_branch=dev/file1.file',
        'path/partitioned-table-2/guid=some-guid-12345/default_branch=dev/file2.file',
        'path/partitioned-table-2/guid=another-guid-12345/default_branch=main/file1.file',
        'path/partitioned-table-2/guid=another-guid-12345/default_branch=main/file2.file',
    ]

    for key in keys:
        s3_bucket.put_object(
            Key=key,
            Body=key
        )

    return s3_bucket


@pytest.fixture()
def glue(mocker):
    glue_data = get_glue_data()
    glue_mock = mocker.MagicMock()

    glue_mock.get_databases.return_value = dict(DatabaseList=glue_data['databases'])

    def get_tables(**kwargs):
        tables = filter(lambda t: t['DatabaseName'] == kwargs['DatabaseName'], glue_data['tables'])
        return dict(TableList=list(tables))

    glue_mock.get_tables.side_effect = get_tables

    def get_partitions(**kwargs):
        pattern = r"^guid NOT IN \((.*)\)$"
        expr = kwargs['Expression']
        matches = re.findall(pattern, expr)

        assert matches

        values = [v.strip(" '") for v in matches[0].split(',')]

        partitions = [p for p in glue_data['partitions'] if p['Values'][0] not in values]
        partitions = filter(lambda p: p['DatabaseName'] == kwargs['DatabaseName']
                            and p['TableName'] == kwargs['TableName'], partitions)
        return dict(Partitions=list(partitions))

    glue_mock.get_partitions.side_effect = get_partitions

    mocker.patch(
        'boto3.client',
        side_effect=lambda s: glue_mock if s == 'glue' else mocker.DEFAULT
    )

    return glue_mock


@pytest.fixture()
def person_repository(mocker):
    mocker.patch.object(PersonRepository, 'get_guids', return_value=['some-guid-12345'])


def test_check_paritionkeys():
    glue_table_stub = {
        'PartitionKeys': [{
            'Name': 'guid',
            'Type': 'STRING'
        },
            {
            'Name': 'location',
            'Type': 'STRING'
        }]
    }
    assert check_partitionkeys(glue_table_stub)


def test_check_paritionkeys_missing():
    glue_table_stub = {
        'PartitionKeys': [{
            'Name': 'language',
            'Type': 'STRING'
        },
            {
            'Name': 'default_branch',
            'Type': 'STRING'
        }]
    }
    assert not check_partitionkeys(glue_table_stub)


def test_uri_transformer():
    uri = 's3://bucket/some/key/prefix/'
    prefix = transform_uri(uri, 'bucket')
    assert prefix == 'some/key/prefix/'


def test_get_guids(person_repository):
    guids = get_guids()
    assert guids == ['some-guid-12345']


def test_glue_get_databases(s3, glue, person_repository):
    handler(None, None)
    glue.get_databases.assert_called_once()


def test_glue_get_tables(s3, glue, person_repository):
    calls = [
        call(DatabaseName='test-database-1'),
        call(DatabaseName='test-database-2')
    ]

    handler(None, None)

    assert glue.get_tables.call_count == 2
    glue.get_tables.assert_has_calls(calls)


def test_glue_get_partitions(s3, glue, person_repository):
    calls = [
        call(
            DatabaseName='test-database-1',
            TableName='partitioned-table-1',
            Expression="guid NOT IN ('some-guid-12345')"),
        call(
            DatabaseName='test-database-2',
            TableName='partitioned-table-2',
            Expression="guid NOT IN ('some-guid-12345')")
    ]

    handler(None, None)

    assert glue.get_partitions.call_count == 2
    glue.get_partitions.assert_has_calls(calls)


def test_glue_delete_partitions(s3, glue, person_repository):
    calls = [
        call(
            DatabaseName='test-database-1',
            TableName='partitioned-table-1',
            PartitionsToDelete=[{
                'Values': [
                    'another-guid-12345',
                    12
                ]
            }]
        ),
        call(
            DatabaseName='test-database-2',
            TableName='partitioned-table-2',
            PartitionsToDelete=[{
                'Values': [
                    'another-guid-12345',
                    'main'
                ]
            }]
        )
    ]

    handler(None, None)

    assert glue.batch_delete_partition.call_count == 2
    glue.batch_delete_partition.assert_has_calls(calls)


def test_deletes_in_s3(s3, glue, person_repository):
    handler(None, None)
    keys = [obj.key for obj in s3.objects.all()]
    assert len(keys) == 7
    assert 'path/partitioned-table-1/guid=some-guid-12345/month=12/file1.file' in keys
    assert 'path/table1/file3.file' in keys
    assert 'path/partitioned-table-2/guid=another-guid-12345/default_branch=main/file2.file' not in keys

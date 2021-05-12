import boto3
from uuid import uuid4
from active_directory_ingest_lambda import handler
from pytest import fixture
from json import load
from os import path, environ
import responses


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data/test_data_ingest.json'), 'r') as json_file:
        yield load(json_file)


def make_test_json(user_details):
    return user_details


def add_ddb_dummy_data(ddb_table):
    for _ in range(5):
        ddb_table.put_item(Item={
            'guid': str(uuid4())
        })


def test_initial_ingest(s3_bucket, test_data, dynamodb_resource):
    responses.add(responses.GET, 'http://10.205.0.5:20201/api/Users', json=make_test_json(test_data), status=200)
    resource = boto3.resource('dynamodb')
    table = resource.Table(environ.get('PERSON_DATA_TABLE'))

    add_ddb_dummy_data(table)
    assert table.item_count == 8

    handler(None, None)

    table = resource.Table(environ.get('PERSON_DATA_TABLE'))
    assert table.item_count == 3

    persons = table.scan()['Items']
    assert persons[0]['displayName'] == 'Per Nordmann'
    assert persons[1]['displayName'] == 'Kari Nordmann'
    assert persons[2]['displayName'] == 'Lisa Nordmann'


def test_filter_service_user(s3_bucket, test_data, dynamodb_resource):
    test_data[2]['userDetails']['isServiceUser'] = True
    responses.add(responses.GET, 'http://10.205.0.5:20201/api/Users', json=make_test_json(test_data), status=200)

    handler(None, None)

    resource = boto3.resource('dynamodb')
    table = resource.Table(environ.get('PERSON_DATA_TABLE'))
    assert table.item_count == 2


def test_find_manager_uuid(s3_bucket, test_data, dynamodb_resource):
    responses.add(responses.GET, 'http://10.205.0.5:20201/api/Users', json=make_test_json(test_data), status=200)
    resource = boto3.resource('dynamodb')
    table = resource.Table(environ.get('PERSON_DATA_TABLE'))

    handler(None, None)

    persons = table.scan()['Items']
    assert persons[0]['managerguid'] == 'e04e18496ba542cf9aa1ede5e2bf100288d96f99'

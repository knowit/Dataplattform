import pytest
import app
import urllib.parse
import boto3


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

    mocker.patch(
        'boto3.client',
        side_effect=lambda service: athena_mock if service == 'athena' else boto3.client(service))


@pytest.fixture(autouse=True)
def setup_mock_athena_result(s3_bucket):
    mock_data = '"col0","col1"\n"row0",0\n"row1",1'
    s3_bucket.Object('query/mock.csv').put(Body=mock_data.encode('utf-8'))


@pytest.fixture
def client():
    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        yield client


def test_root_spec(client):
    response = client.get('/data/')
    assert response.json['info']['title'] == "Dataplattform Data API"


def test_spec_spec(client):
    response = client.get('/data/spec')
    assert response.json['info']['title'] == "Dataplattform Data API"


def test_query_missing_args(client):
    response = client.get('/data/query')
    assert 'error' in response.json and '500' in response.status


def test_query_get_json(client):
    response = client.get(f'/data/query?sql={urllib.parse.quote("select * from test")}')
    assert len(response.json) == 2


def test_query_post_json(client):
    response = client.post('/data/query', json={'sql': 'select * from test'})
    assert len(response.json) == 2


def test_query_get_csv(client):
    response = client.get(f'/data/query?sql={urllib.parse.quote("select * from test")}&format=csv')
    text = response.data.decode()
    assert len(text) > 0 and 'col0' in text


def test_query_post_csv(client):
    response = client.post('/data/query', json={'sql': 'select * from test', 'format': 'csv'})
    text = response.data.decode()
    assert len(text) > 0 and 'col0' in text


def test_query_bad_sql_insert(client):
    response = client.get(f'/data/query?sql={urllib.parse.quote("insert into test (col0) values (1)")}')
    assert 'error' in response.json and '500' in response.status


def test_query_bad_sql_delete(client):
    response = client.get(f'/data/query?sql={urllib.parse.quote("delete from test where col0 = 1")}')
    assert 'error' in response.json and '500' in response.status


def test_query_bad_sql_update(client):
    response = client.get(f'/data/query?sql={urllib.parse.quote("update test set col0 = 1")}')
    assert 'error' in response.json and '500' in response.status

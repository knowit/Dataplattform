import pytest
import app
import urllib.parse


@pytest.fixture
def client():
    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        yield client


def test_query_missing_args(client):
    response = client.get('/data/query')
    assert 'errors' in response.json and '400' in response.status


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
    assert 'Illegal SQL' in response.json['body'] and 400 == response.json['statusCode']


def test_query_bad_sql_delete(client):
    response = client.get(f'/data/query?sql={urllib.parse.quote("delete from test where col0 = 1")}')
    assert 'Illegal SQL' in response.json['body'] and 400 == response.json['statusCode']


def test_query_bad_sql_update(client):
    response = client.get(f'/data/query?sql={urllib.parse.quote("update test set col0 = 1")}')
    assert 'Illegal SQL' in response.json['body'] and 400 == response.json['statusCode']

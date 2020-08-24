import pytest
import app


@pytest.fixture
def client():
    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        yield client


def test_root_spec(client):
    response = client.get('/')
    assert response.status == '200 OK'


def test_database_route(client, glue):
    response = client.get('/database/test_database')
    assert response.status == '200 OK'


def test_database_content(client, glue):
    response = client.get('/database/test_database')
    res = response.json

    assert res is not None
    assert res['tables'][0] == 'test_table'
    assert res['name'] == 'test_database'


def test_database_route_404(client, glue):
    response = client.get('/database/test_database1')
    assert response.status == '404 NOT FOUND'


def test_database_route_404_ignore(client, glue):
    response = client.get('/database/default')
    assert response.status == '404 NOT FOUND'


def test_database_table_route_404_ignore(client, glue):
    response = client.get('/database/default/test_table')
    assert response.status == '404 NOT FOUND'


def test_table_route(client, glue):
    response = client.get('/database/test_database/table/test_table')
    assert response.status == '200 OK'


def test_database_table_route_404(client, glue):
    response = client.get('/database/test_database/table/test_table1')
    assert response.status == '404 NOT FOUND'


def test_database_table_content(client, glue):
    response = client.get('/database/test_database/table/test_table')
    res = response.json
    assert res['columns'] is not None
    assert res['columns'][0]['name'] == 'col1'


""" not able to test, get_databases() not implemented in moto

def test_table_route_404(client, glue):
    response = client.get('/table/test_table1')
    assert response.status == '404 NOT FOUND'


def test_table_route_404_ignore(client, glue):
    response = client.get('/table/default')
    assert response.status == '404 NOT FOUND'


def test_table_content(client, glue):
    response = client.get('/table/test_table')
    res = response.json
    assert res['columns'] is not None
    assert res['columns'][0]['name'] == 'col1'

def test_databases_route(client, glue):
    response = client.get('/database/')
    assert response.status == '200 OK'

"""

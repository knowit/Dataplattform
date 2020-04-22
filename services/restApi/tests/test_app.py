import pytest
import app


@pytest.fixture
def client():
    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        yield client


def test_get_all_open(client):
    response = client.get('/api/v1/test-open/')
    assert (b'{"name": "Testersen", "age": 73}' in response.data and
            b'{"name": "Bjarne", "age": 7}' in response.data and
            b'{"name": "Potet", "age": 22}' in response.data)


def test_get_person_by_name_open(client):
    response = client.get('/api/v1/test-open/Potet')
    assert b'[{"name": "Potet", "age": 22}]' in response.data

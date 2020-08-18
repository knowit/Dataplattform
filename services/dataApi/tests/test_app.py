import pytest
import app


@pytest.fixture
def client():
    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        yield client


def test_simple(client):
    response = client.get('/')
    assert response.data

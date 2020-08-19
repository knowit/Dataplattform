import pytest
import app
import boto3


@pytest.fixture
def client():
    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        yield client


def test_root_spec(client):
    response = client.get('/')
    assert response is not None
    assert response.status == '200 OK'

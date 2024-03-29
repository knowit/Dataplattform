from cvpartner.cv_partner_ingest_lambda import handler, offset_size
from json import loads
import responses
from pytest import fixture
from os import environ


@fixture(autouse=True)
def mock_save_document(mocker):
    mocker.patch('cvpartner.cv_partner_ingest_lambda.save_document')


def add_dummy_data(bucket, prefix):
    dummy = [
        f'{prefix}/dummy.txt',
        f'{prefix}/dummy2.txt',
        f'{prefix}/dummy3.txt',
        f'{prefix}/dummy4.txt',
        f'{prefix}/dummy5.txt',
        f'{prefix}/dummy6.txt',
    ]
    for item in dummy:
        bucket.put_object(Body='some data', Key=item)


def make_test_json(user_id, cv_id, ext):
    return {
        'cvs': [
            {
                'cv': {
                    'user_id': user_id,
                    'id': cv_id,
                    'image': {
                        'thumb': {
                            'url': f'https://cvpartner.com/test.{ext}'
                        }
                    }
                }
            }
        ]
    }


def cv_test_json(cv_id):
    return [
        {
            'cv': {
                '_id': cv_id,
                'born_day': 11,
                'born_month': 12
            }
        }
    ]


def test_initial_ingest(s3_bucket, s3_public_bucket):
    base_url = 'https://knowittest2.cvpartner.com/api'

    public_prefix = environ.get('PUBLIC_PREFIX')
    datalake_prefix = environ.get('ACCESS_PATH')+"raw"

    add_dummy_data(s3_public_bucket, public_prefix)
    add_dummy_data(s3_bucket, datalake_prefix)

    assert len(list(s3_public_bucket.objects.filter(Prefix=public_prefix))) == 6
    assert len(list(s3_bucket.objects.filter(Prefix=datalake_prefix))) == 6

    user_id = '1'
    cv_id = '2'
    responses.add(responses.GET,
                  f'{base_url}/v3/search?office_ids[]=objectnet_id&office_ids[]=sor_id&offset=0&size={offset_size}',
                  json=make_test_json(user_id, cv_id, 'jpg'), status=200)
    responses.add(responses.GET, f'{base_url}/v3/cvs/{user_id}/{cv_id}',
                  json=cv_test_json(cv_id), status=200)
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data'][0]['user_id'] == user_id
    assert data['data'][0]['default_cv_id'] == cv_id
    cv_link_correct = f'{base_url}/v1/cvs/download/{user_id}/{cv_id}/{{LANG}}/{{FORMAT}}/'
    assert data['data'][0]['cv_link'] == cv_link_correct

    assert len(list(s3_public_bucket.objects.filter(Prefix=public_prefix))) == 0
    assert len(list(s3_bucket.objects.filter(Prefix=datalake_prefix))) == 1
    assert 'jpg' in data['data'][0]['image_key']


def test_png(s3_bucket):
    base_url = 'https://knowittest2.cvpartner.com/api'
    user_id = '1'
    cv_id = '2'
    responses.add(responses.GET,
                  f'{base_url}/v3/search?office_ids[]=objectnet_id&office_ids[]=sor_id&offset=0&size={offset_size}',
                  json=make_test_json(user_id, cv_id, 'png'), status=200)
    responses.add(responses.GET, f'{base_url}/v3/cvs/{user_id}/{cv_id}',
                  json=cv_test_json(cv_id), status=200)
    handler(None, None)
    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert 'png' in data['data'][0]['image_key']

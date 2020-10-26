from cv_partner_ingest_lambda import handler, url, url_v1, offset_size
from json import loads
import responses
from pytest import fixture
import re


@fixture(autouse=True)
def launch_lambda_mock(mocker):
    mocker.patch('dataplattform.common.helper.Helper.launch_async_lambda')


def make_test_json(user_id, cv_id):
    return {
        'cvs': [
            {
                'cv': {
                    'user_id': user_id,
                    'id': cv_id,
                    'image': {
                        'thumb': {
                            'url': 'https://cvpartner.com'
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


def test_initial_ingest(s3_bucket):
    user_id = '1'
    cv_id = '2'

    responses.add(responses.GET,
                  f'{url}/search?office_ids[]=objectnet_id&office_ids[]=sor_id&offset=0&size={offset_size}',
                  json=make_test_json(user_id, cv_id), status=200)
    responses.add(responses.GET, f'{url}/cvs/{user_id}/{cv_id}',
                  json=cv_test_json(cv_id), status=200)
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data'][0]['user_id'] == user_id
    assert data['data'][0]['default_cv_id'] == cv_id
    assert re.fullmatch(r'public/[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}.jpg', data['data'][0]['image_key'])
    assert re.fullmatch(r'private/[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}.pdf', data['data'][0]['cv_no_pdf'])
    assert re.fullmatch(r'private/[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}.pdf', data['data'][0]['cv_int_pdf'])
    assert re.fullmatch(r'private/[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}.docx', data['data'][0]['cv_no_docx'])
    assert re.fullmatch(r'private/[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}.docx', data['data'][0]['cv_int_docx'])
    cv_link_correct = url_v1 + f'/cvs/download/{user_id}/{cv_id}/{{LANG}}/{{FORMAT}}/'
    assert data['data'][0]['cv_link'] == cv_link_correct

from cv_partner_ingest_lambda import handler, url, url_v1
from json import loads
from dataplattform.common.aws import SSM
import responses


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
    size = 1000

    objectnet_id = SSM(with_decryption=False).get('cv_partner_objectnet_id')
    sor_id = SSM(with_decryption=False).get('cv_partner_sor_id')

    responses.add(responses.GET,
                  url + f'/search?office_ids[]={objectnet_id}&office_ids[]={sor_id}&offset=0&size={size}',
                  json=make_test_json(user_id, cv_id), status=200)
    responses.add(responses.GET, url + f'/cvs/{user_id}/{cv_id}'.format(user_id=user_id, cv_id=cv_id),
                  json=cv_test_json(cv_id), status=200)
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data is not None
    assert data['data'][0]['user_id'] == user_id
    assert data['data'][0]['default_cv_id'] == cv_id
    assert data['data'][0]['image'] is not None
    cv_link_correct = url_v1 + f'/cvs/download/{user_id}/{cv_id}/no/pdf/'
    assert data['data'][0]['cv_link'] == cv_link_correct

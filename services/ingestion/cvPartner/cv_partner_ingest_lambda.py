from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.raw_storage import RawStorage
from dataplattform.common.aws import SSM
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import requests
import urllib.request as request

url = 'https://knowit.cvpartner.com/api/v3'
url_v1 = 'https://knowit.cvpartner.com/api/v1'
offset_size = 1000
handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:

    objectnet_id = SSM(with_decryption=False).get('cv_partner_objectnet_id')
    sor_id = SSM(with_decryption=False).get('cv_partner_sor_id')
    api_token = SSM(with_decryption=True).get('cv_partner_api_token')

    res = requests.get(f'{url}/search?office_ids[]={objectnet_id}&office_ids[]={sor_id}&offset=0&size={offset_size}',
                       headers={'Authorization': f'Bearer {api_token}'})

    data_json = res.json()

    def get_jpg(image_path):
        if image_path['url'] is None:
            return
        image_res = request.urlopen(image_path['url'])
        if (image_res.status != 200):
            return
        return image_res.read()

    def get_person(person):
        return {
            'user_id': person['cv']['user_id'],
            'default_cv_id': person['cv']['id'],
            'image_key': RawStorage().write_to_public_bucket(get_jpg(person['cv']['image']['thumb']), 'jpg'),
            'cv_link': url_v1 + f"/cvs/download/{person['cv']['user_id']}/{person['cv']['id']}/{{LANG}}/{{FORMAT}}/"
        }

    def get_cv(user_id, cv_id):
        cv = requests.get(url + f'/cvs/{user_id}/{cv_id}',
                          headers={'Authorization': f'Bearer {api_token}'})
        return cv.json()

    def get_list_of_users(data):
        list_of_users = []
        for person in data['cvs']:
            user = get_person(person)
            user['cv'] = get_cv(user['user_id'], user['default_cv_id'])
            list_of_users.append(user)
        return list_of_users

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=get_list_of_users(data_json))

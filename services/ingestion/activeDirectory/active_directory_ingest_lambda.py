from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import requests

url = 'http://10.205.0.5:20201/api/Users'
handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:
    res = requests.get(f'{url}')
    data_json = res.json()

    def get_list_of_users(data):
        list_of_users = []
        for user in data:
            user_details = user['userDetails']
            list_of_users.append(user_details)
        return list_of_users

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=get_list_of_users(data_json))

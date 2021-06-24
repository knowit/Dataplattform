from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
import requests

handler = IngestHandler()


@handler.ingest(overwrite=True)
def ingest(event) -> Data:
    url = SSM(with_decryption=False).get('kompetansekartlegging_api_url')
    api_token = SSM(with_decryption=True).get('kompetansekartlegging_api_key')
    users = requests.get(f'{url}/users', headers={'x-api-key': api_token}).json()
    answers = requests.get(f'{url}/answers', headers={'x-api-key': api_token}).json()
    catalogs = requests.get(f'{url}/catalogs', headers={'x-api-key': api_token}).json()

    newest_catalog = answers[0]['formDefinitionID']

    categories = requests.get(f'{url}/catalogs/{newest_catalog}/categories',
                              headers={'x-api-key': api_token}).json()

    questions = requests.get(f'{url}/catalogs/{newest_catalog}/questions',
                             headers={'x-api-key': api_token}).json()

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data={'answers': answers,
              'users': users,
              'catalogs': catalogs,
              'categories': categories,
              'questions': questions}
    )

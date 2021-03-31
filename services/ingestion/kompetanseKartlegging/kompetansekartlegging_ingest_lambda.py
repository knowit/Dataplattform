from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
import requests

base_url = 'https://jn76t2rune.execute-api.eu-central-1.amazonaws.com/dev'

handler = IngestHandler()


@handler.ingest()
def handler(event) -> Data:
    api_token = SSM(with_decryption=True).get('API_KEY')
    users = requests.get(f'{base_url}/users', headers={'x-api-key': api_token}).json()
    answers = requests.get(f'{base_url}/answers', headers={'x-api-key': api_token}).json()
    catalogs = requests.get(f'{base_url}/catalogs', headers={'x-api-key': api_token}).json()

    newest_catalog = answers[0]['formDefinitionID']
    categories = requests.get(f'{base_url}/catalogs/{newest_catalog}/categories', headers={'x-api-key': api_token}).json()
    questions = requests.get(f'{base_url}/catalogs/{newest_catalog}/questions', headers={'x-api-key': api_token}).json()

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data={'answers': answers,
              'users': users,
              'catalogs': catalogs,
              'categories': categories,
              'questions': questions}
    )

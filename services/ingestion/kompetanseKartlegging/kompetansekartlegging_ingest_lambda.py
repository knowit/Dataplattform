from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
import requests
from os import environ

handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:
    base_url = 'https://api.kompetanse.knowit.no'
    stage = environ['STAGE']

    if stage == 'dev':
        base_url += '/dev'

    api_token = SSM(with_decryption=True).get(f'kompetansekartlegging_api_key_{stage}')
    users = requests.get(f'{base_url}/users', headers={'x-api-key': api_token}).json()
    answers = requests.get(f'{base_url}/answers', headers={'x-api-key': api_token}).json()
    catalogs = requests.get(f'{base_url}/catalogs', headers={'x-api-key': api_token}).json()

    newest_catalog = answers[0]['formDefinitionID']

    categories = requests.get(f'{base_url}/catalogs/{newest_catalog}/categories',
                              headers={'x-api-key': api_token}).json()

    questions = requests.get(f'{base_url}/catalogs/{newest_catalog}/questions',
                             headers={'x-api-key': api_token}).json()

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data={'answers': answers,
              'users': users,
              'catalogs': catalogs,
              'categories': categories,
              'questions': questions}
    )

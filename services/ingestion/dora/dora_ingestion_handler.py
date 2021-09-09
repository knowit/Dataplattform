from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
import requests
from dateutil.parser import isoparse

handler = IngestHandler()
url = 'https://api.github.com/repos/knowit/Dataplattform/events'
branch_url = 'https://api.github.com/repos/knowit/dataplattform'


@handler.ingest()
def ingest(event) -> Data:
    api_token = SSM(with_decryption=True).get('github_api_token')
    res = requests.get(url, headers={'Authorization': f'Bearer {api_token}'})
    events = res.json()

    while 'next' in res.links.keys():
        res = requests.get(res.links['next']['url'])
        events.extend(res.json())

    def retrieve_default_branch():
        api_token_default_branch = SSM(with_decryption=True).get('github_api_token')
        res_default_branch = requests.get(branch_url, headers={'Authorization': f'Bearer {api_token_default_branch}'})
        event_default_branch = res_default_branch.json()
        return event_default_branch['default_branch']

    default_branch = retrieve_default_branch()

    def to_timestamp(date):
        return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

    def data_point(event):
        if event['type'] != "PullRequestEvent" or event['payload']['pull_request']['merged_at'] is None or event['payload']['pull_request']['base']['ref'] != default_branch:
            return None
        return {
            'id': event['id'],
            'type': event['type'],
            'merged_at': to_timestamp(event['payload']['pull_request']['merged_at']),
            'created_at': to_timestamp(event['payload']['pull_request']['created_at']),
            'base-ref': event['payload']['pull_request']['base']['ref']
        }

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=[data_point(event) for event in events if data_point(event) != None])

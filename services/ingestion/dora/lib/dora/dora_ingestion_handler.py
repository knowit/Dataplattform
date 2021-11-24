from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
import requests
from dateutil.parser import isoparse
import boto3

handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:
    client = boto3.client('ssm')
    repos = client.get_parameters_by_path(
        Path='/dev/dora/github/repos/',
        Recursive=True
    )

    def retrieve_events_from_repo(repo):
        events = []
        repo_name = repo['Name'].rsplit("/", 1)[1]
        api_token = SSM(with_decryption=True).get('github/apikey/' + repo_name)
        res = requests.get(SSM(with_decryption=False).get('github/repos/' + repo_name),
                           headers={'Authorization': f'Bearer {api_token}'})
        if not events:
            events = res.json()
        else:
            events.extend(res.json())

        while 'next' in res.links.keys():
            res = requests.get(res.links['next']['url'])
            events.extend(res.json())

        return events

    def retrieve_default_branch(repo):
        try:
            return SSM(with_decryption=False).get('github/prod/' + repo)
        except:
            api_token_default_branch = SSM(with_decryption=True).get('github/apikey/' + repo)
            res_default_branch = requests.get(SSM(with_decryption=False).get('github/defaultBranch/' + repo),
                                            headers={'Authorization': f'Bearer {api_token_default_branch}'})
            event_default_branch = res_default_branch.json()
            return event_default_branch['default_branch']

    def to_timestamp(date):
        return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

    def data_point(event, default_branch):
        if event['type'] != "PullRequestEvent" or event['payload']['pull_request']['merged_at'] is None or \
                event['payload']['pull_request']['base']['ref'] != default_branch:
            return None
        return {
            'id': event['id'],
            'name': event['repo']['name'],
            'type': event['type'],
            'merged_at': to_timestamp(event['payload']['pull_request']['merged_at']),
            'created_at': to_timestamp(event['payload']['pull_request']['created_at']),
            'base-ref': event['payload']['pull_request']['base']['ref'],
            'default_branch': default_branch,
            'source': 'github'
        }

    def add_data_points():
        data = []
        for repo in repos['Parameters']:
            events = retrieve_events_from_repo(repo)
            default_branch = retrieve_default_branch(repo['Name'].rsplit("/", 1)[1])
            data.extend(
                data_point(event, default_branch) for event in events if data_point(event, default_branch) is not None)
        return data

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=add_data_points())

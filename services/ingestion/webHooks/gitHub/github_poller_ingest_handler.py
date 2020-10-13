from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.aws import SSM
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import requests
from dateutil.parser import isoparse

url = 'https://api.github.com/orgs/knowit/repos'

handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:
    api_token = SSM(with_decryption=True).get('github_api_token')
    res = requests.get(url, headers={'Authorization': f'Bearer {api_token}'})

    repos = res.json()
    while 'next' in res.links.keys():
        res = requests.get(res.links['next']['url'])
        repos.extend(res.json())

    def to_timestamp(date):
        return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

    def data_point(repo):   # TODO: Move hard coding of values to another file?
        return {
            'id': repo['id'],
            'name': repo['name'],
            'description': repo['description'],
            'url': repo['url'],
            'html_url': repo['html_url'],
            'owner': repo['owner']['login'],
            'created_at': to_timestamp(repo['created_at']),
            'updated_at': to_timestamp(repo['updated_at']),
            'pushed_at': to_timestamp(repo['pushed_at']),
            'language': repo['language'],
            'forks_count': repo['forks_count'],
            'stargazers_count': repo['stargazers_count'],
            'default_branch': repo['default_branch']
        }

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=[data_point(repo) for repo in repos])

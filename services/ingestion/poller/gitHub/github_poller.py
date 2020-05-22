from dataplattform.common.handler import Handler
from dataplattform.common.aws import SSM
from dataplattform.common.schema import Data, Metadata
from dataplattform.query.engine import Athena
from typing import Dict
from datetime import datetime
import requests
import dateutil.parser
import pandas as pd

url = 'https://api.github.com/orgs/knowit/repos'

handler = Handler()
ath = Athena()


@handler.ingest()
def ingest(event) -> Data:
    api_token = SSM(with_decryption=True).get('github_api_token')
    res = requests.get(url, headers={'Authorization': f'Bearer {api_token}'})

    repos = res.json()
    while 'next' in res.links.keys():
        res = requests.get(res.links['next']['url'])
        repos.extend(res.json())

    def convert_ISO8601_to_timestamp(time_str):
        return int(dateutil.parser.parse(time_str).timestamp())

    def data_point(repo):   # TODO: Move hard coding of values to another file?
        return {
            'id': repo['id'],
            'name': repo['name'],
            'description': repo['description'],
            'url': repo['url'],
            'html_url': repo['html_url'],
            'owner': repo['owner']['login'],
            'created_at': convert_ISO8601_to_timestamp(repo['created_at']),
            'updated_at': convert_ISO8601_to_timestamp(repo['updated_at']),
            'pushed_at': convert_ISO8601_to_timestamp(repo['pushed_at']),
            'language': repo['language'],
            'forks_count': repo['forks_count'],
            'stargazers_count': repo['stargazers_count'],
            'default_branch': repo['default_branch']
        }

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=[data_point(repo) for repo in repos])


@handler.process(partitions={'github_knowit_repos': ['language', 'default_branch'],
                             'github_knowit_repo_status': []})
def process(data) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        repos_dataframe = pd.json_normalize(payload)
        repos_dataframe['time'] = int(metadata['timestamp'])
        return repos_dataframe

    # TODO: Move to separate file, together with main table construction in ingest
    repos_table_coloumns = ['id',
                            'name',
                            'description',
                            'url',
                            'html_url',
                            'owner',
                            'created_at',
                            'language',
                            'default_branch',
                            'time']

    repos_status_table_coloumns = ['id',
                                   'updated_at',
                                   'pushed_at',
                                   'forks_count',
                                   'stargazers_count',
                                   'time']

    github_dataframe = pd.concat([make_dataframe(d) for d in data])

    reg_ids_df = ath.from_('github_knowit_repos').select('id').execute(ath).as_pandas()
    github_dataframe = github_dataframe[~github_dataframe.id.isin(reg_ids_df.id)]

    repos_table = github_dataframe.loc[:, repos_table_coloumns]
    repos_status_table = github_dataframe.loc[:, repos_status_table_coloumns]

    return {
        'github_knowit_repos': repos_table,
        'github_knowit_repo_status': repos_status_table
    }

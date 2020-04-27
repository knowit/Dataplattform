from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from typing import Dict
from datetime import datetime

import requests
import dateutil.parser

import pandas as pd

url = 'https://api.github.com/orgs/knowit/repos'

handler = Handler()


@handler.ingest()
def ingest(event) -> Data:
    def fetch_github_data(url):

        res = requests.get(url)
        repos = res.json()
        while 'next' in res.links.keys():
            res = requests.get(res.links['next']['url'])
            repos.extend(res.json())

        def convert_ISO8601_to_timestamp(time_str):
            return int(dateutil.parser.parse(time_str).timestamp())

        def data_point(repo_list):    # TODO: Move hard coding of values to another file?
            return {'id': repo_list['id'],
                    'name': repo_list['name'],
                    'description': repo_list['description'],
                    'url': repo_list['url'],
                    'html_url': repo_list['html_url'],
                    'owner': repo_list['owner']['login'],
                    'created_at': convert_ISO8601_to_timestamp(repo_list['created_at']),
                    'updated_at': convert_ISO8601_to_timestamp(repo_list['updated_at']),
                    'pushed_at': convert_ISO8601_to_timestamp(repo_list['pushed_at']),
                    'language': repo_list['language'],
                    'forks_count': repo_list['forks_count'],
                    'stargazers_count': repo_list['stargazers_count'],
                    'default_branch': repo_list['default_branch']
                    }

        return [data_point(repos[i]) for i in range(len(repos))]

    tmp = Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=fetch_github_data(url))
    return tmp

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
    repos_table = github_dataframe.loc[:, repos_table_coloumns]
    repos_status_table = github_dataframe.loc[:, repos_status_table_coloumns]

    return {
        'github_knowit_repos': repos_table,
        'github_knowit_repo_status': repos_status_table
    }

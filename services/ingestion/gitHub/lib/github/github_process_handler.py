from dataplattform.common.handlers.process import ProcessHandler
from dataplattform.query.engine import Athena
from typing import Dict
import pandas as pd
from pyathena.error import OperationalError

handler = ProcessHandler()
ath = Athena()


@handler.process(partitions={'github_knowit_repos': ['language', 'default_branch'],
                             'github_knowit_repo_status': []})
def process(data, events) -> Dict[str, pd.DataFrame]:
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

    try:
        reg_ids_df = ath.from_('github_knowit_repos').select(
            'id').execute(ath).as_pandas()
        github_dataframe = github_dataframe[~github_dataframe.id.isin(
            reg_ids_df.id)]

        repos_table = github_dataframe.loc[:, repos_table_coloumns]
        repos_status_table = github_dataframe.loc[:, repos_status_table_coloumns]

    except OperationalError as err:  # Workaround for inital construction of tables when changing names
        print(f'OperationalError {err}')

    return {
        'github_knowit_repos': repos_table,
        'github_knowit_repo_status': repos_status_table
    }

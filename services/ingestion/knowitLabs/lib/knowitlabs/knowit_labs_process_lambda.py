from dataplattform.common.handlers.process import ProcessHandler
from dataplattform.query.engine import Athena
import pandas as pd
from typing import Dict
from pyathena.error import OperationalError


handler = ProcessHandler()
ath = Athena()


@handler.process(partitions={})
def process(data, events) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        df = pd.json_normalize(payload)
        df['time'] = int(metadata['timestamp'])
        return df

    blog_coloumns = [
        'medium_id',
        'author_name',
        'author_username',
        'title',
        'created_at',
        'first_published_at',
        'word_count',
        'reading_time',
        'url',
        'language']

    blog_update_coloumns = [
        'medium_id',
        'updated_at',
        'latest_published_at',
        'total_claps',
        'total_unique_claps',
        'comments_count',
        'time']

    df = pd.concat([make_dataframe(d) for d in data])
    posts_df = df[blog_coloumns].copy()
    updates_df = df[blog_update_coloumns].copy()

    try:
        reg_ids_df = ath.from_('knowit_labs_blog_posts').select('medium_id').execute(ath).as_pandas()
        posts_df = posts_df[~posts_df.medium_id.isin(reg_ids_df.medium_id)]
    except OperationalError as err:  # Workaround for inital construction of tables when changing names
        print(f'OperationalError {err}')

    return {
        'knowit_labs_blog_posts': posts_df,
        'knowit_labs_blog_updates': updates_df
    }

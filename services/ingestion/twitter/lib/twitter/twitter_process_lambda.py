from dataplattform.common.handlers.process import ProcessHandler
from dataplattform.query.engine import Athena
import pandas as pd
from typing import Dict
from pyathena.error import OperationalError


handler = ProcessHandler()
ath = Athena()


def as_separated_list(entities, value_key, separator=';'):
    return separator.join([
        items[value_key] for items in entities
    ]) if entities else None


@handler.process(partitions={
    'twitter_timeline': ['user_screen_name'],
    'twitter_account_status_update': ['screen_name']
})
def process(data, events) -> Dict[str, pd.DataFrame]:
    search_data, timeline_data, accounts_data = list(zip(*[
        (
            d['data']['search'], d['data']['timeline'],
            [dict(x, time=int(d['metadata']['timestamp']))
             for x in d['data']['accounts']]
        )
        for d in [d.json() for d in data]]))

    search_data = pd.concat([pd.DataFrame.from_records(d)
                            for d in search_data])
    timeline_data = pd.concat([pd.DataFrame.from_records(d)
                              for d in timeline_data])
    accounts_data = pd.concat([pd.DataFrame.from_records(d)
                              for d in accounts_data])

    try:
        in_tweets_df = ath.from_('twitter_tweets').select(
            'tweet_id').execute(ath).as_pandas()
        in_timeline_df = ath.from_('twitter_timeline').select(
            'tweet_id').execute(ath).as_pandas()
        search_data = search_data[~search_data.tweet_id.isin(
            in_tweets_df.tweet_id)]
        timeline_data = timeline_data[~timeline_data.tweet_id.isin(
            in_timeline_df.tweet_id)]

    except OperationalError as err:  # Workaround for inital construction of tables when changing names
        print(f'OperationalError {err}')

    return {
        'twitter_tweets': search_data,
        'twitter_timeline': timeline_data,
        'twitter_account_status_update': accounts_data
    }

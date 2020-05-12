from dataplattform.common.handler import Handler
from dataplattform.common.aws import SSM
from dataplattform.common.schema import Data, Metadata
from dataplattform.query.engine import Athena
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict
from tweepy import OAuthHandler, API, Cursor


handler = Handler()
ath = Athena()


def as_separated_list(entities, value_key, separator=';'):
    return separator.join([
        items[value_key] for items in entities
    ]) if entities else None


@handler.ingest()
def ingest(event) -> Data:
    consumer_key, consumer_secret, access_token, access_secret = SSM(with_decryption=True).get(
        'twitter_comsumer_key', 'twitter_comsumer_secret', 'twitter_access_token', 'twitter_access_secret')

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    api = API(auth)

    search_args = ['knowit', '"knowit objectnet"', '"knowit amende"',
                   '"knowit solutions"', '"knowit experience"', '"knowit insight"',
                   'knowitab', 'knowitnorge', 'knowit norge', '"knowit stavanger"',
                   'knowit bergen', 'knowit oslo', 'knowit sverige', 'knowit norway',
                   'knowit sweden', 'knowit finland', 'knowitx']

    knowit_accounts = [
        'knowitnorge',
        'knowitab',
        'KnowitSuomi',
        'knowitx']

    def search_data():
        search_result = np.hstack([
            [item for item in Cursor(
                api.search,
                q=arg,
                lang='no' if arg == 'knowit' else None,
                tweet_mode='extended').items() if item.user.screen_name not in knowit_accounts]
            for arg in search_args])

        return [
            {
                'tweet_id': item.id,
                'created_at': int(item.created_at.timestamp()),
                'text': item.full_text,
                'is_retweet': item.full_text.startswith('RT @'),
                'favorite_count': item.favorite_count,
                'retweet_count': item.retweet_count,
                'language': item.lang,
                'hashtags': as_separated_list(item.entities['hashtags'], 'text'),
                'place': item.place.full_name if item.place else None,
                'reply_to':
                    item.in_reply_to_screen_name
                    if item.in_reply_to_screen_name
                    and item.in_reply_to_screen_name in knowit_accounts else None
            } for item in search_result]

    def timeline_data():
        timeline_result = np.hstack([
            [item for item in Cursor(
                api.user_timeline,
                screen_name=account,
                tweet_mode='extended').items()]
            for account in knowit_accounts])

        return [
            {
                'tweet_id': item.id,
                'created_at': int(item.created_at.timestamp()),
                'user_screen_name': item.user.screen_name,
                'text': item.full_text,
                'is_retweet': item.full_text.startswith('RT @'),
                'favorite_count': item.favorite_count,
                'retweet_count': item.retweet_count,
                'language': item.lang,
                'hashtags': as_separated_list(item.entities['hashtags'], 'text'),
                'mentions': as_separated_list(item.entities['user_mentions'], 'screen_name'),
                'user_name': item.user.name
            } for item in timeline_result]

    def account_data():
        account_result = [
            api.get_user(screen_name=account)
            for account in knowit_accounts]

        return [
            {
                'user_id': item.id,
                'screen_name': item.screen_name,
                'name': item.name,
                'statuses_count': item.statuses_count,
                'followers_count': item.followers_count,
                'favourites_count': item.favourites_count,
                'friends_count': item.friends_count,
                'listed_count': item.listed_count
            } for item in account_result]

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data={
            'search': search_data(),
            'timeline': timeline_data(),
            'accounts': account_data()
        })


@handler.process(partitions={
    'twitter_timeline': ['user_screen_name'],
    'twitter_account_status_update': ['screen_name']
})
def process(data) -> Dict[str, pd.DataFrame]:
    search_data, timeline_data, accounts_data = list(zip(*[
        (
            d['data']['search'], d['data']['timeline'],
            [dict(x, time=int(d['metadata']['timestamp'])) for x in d['data']['accounts']]
        )
        for d in [d.json() for d in data]]))

    search_data = pd.concat([pd.DataFrame.from_records(d) for d in search_data])
    timeline_data = pd.concat([pd.DataFrame.from_records(d) for d in timeline_data])
    accounts_data = pd.concat([pd.DataFrame.from_records(d) for d in accounts_data])

    in_tweets_df = ath.from_('twitter_tweets').select('tweet_id').execute(ath).as_pandas()
    in_timeline_df = ath.from_('twitter_timeline').select('tweet_id').execute(ath).as_pandas()

    search_data = search_data[~search_data.tweet_id.isin(in_tweets_df.tweet_id)]
    timeline_data = timeline_data[~timeline_data.tweet_id.isin(in_timeline_df.tweet_id)]

    return {
        'twitter_tweets': search_data,
        'twitter_timeline': timeline_data,
        'twitter_account_status_update': accounts_data
    }

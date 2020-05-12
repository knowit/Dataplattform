from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.query.engine import Athena
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import numpy as np
from typing import Dict
import re


handler = Handler()
ath = Athena()


@handler.ingest()
def ingest(event) -> Data:
    def scrape_archive_urls():
        def scrape_url(url, pattern):
            response = requests.get(url)
            soup = BeautifulSoup(response.content, features='lxml')
            urls = list(set([a['href'] for a in soup.find_all(
                href=lambda href: href and re.match(pattern, href))]))
            return urls if urls else [url]

        blog_year_urls = scrape_url('https://knowitlabs.no/archive',
                                    r'https:\/\/knowitlabs\.no\/archive\/\d{4}')

        return np.hstack([
            scrape_url(url, r'https:\/\/knowitlabs\.no\/archive\/\d{4}\/\d{2}')
            for url in blog_year_urls])

    def scrape_article_data(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, features='lxml')

        def map_content(content):
            json_content = json.loads(content[content.find('{'):content.rfind('}')+1])
            user_map = json_content.get('references', {}).get('User', {})
            return [
                {
                    'medium_id': post['id'],
                    'author_name': user_map.get(post['creatorId'], {}).get('name', ''),
                    'author_username': user_map.get(post['creatorId'], {}).get('username', ''),
                    'title':  post['title'],
                    'created_at': int(float(post['createdAt'])/1000.0),
                    'updated_at': int(float(post['updatedAt'])/1000.0),
                    'first_published_at': int(float(post['firstPublishedAt'])/1000.0),
                    'latest_published_at': int(float(post['latestPublishedAt'])/1000.0),
                    'word_count': post['virtuals']['wordCount'],
                    'reading_time': post['virtuals']['readingTime'],
                    'total_claps': post['virtuals']['totalClapCount'],
                    'total_unique_claps': post['virtuals']['recommends'],
                    'language': post['detectedLanguage'],
                    'url': f'https://knowitlabs.no/{post["uniqueSlug"]}',
                    'comments_count': post['virtuals']['responsesCreatedCount']
                }
                for post in json_content.get('references', {}).get('Post', {}).values()
            ]

        contents = [
            tag.string for tag in
            soup.find_all('script', string=lambda s: s and s.startswith('// <![CDATA[\nwindow["obvInit"]({'))]

        return np.hstack([map_content(content) for content in contents])

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data=np.hstack([scrape_article_data(url) for url in scrape_archive_urls()]))


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
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

    reg_ids_df = ath.from_('blog_posts').select('medium_id').execute(ath).as_pandas()
    posts_df = posts_df[~posts_df.medium_id.isin(reg_ids_df.medium_id)]

    return {
        'blog_posts': posts_df,
        'blog_updates': updates_df
    }

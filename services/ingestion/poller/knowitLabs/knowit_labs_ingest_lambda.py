from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import json
import numpy as np
import re


handler = IngestHandler()


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

from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
from json import loads
from typing import Dict, AnyStr
import pandas as pd
from dataclasses import dataclass
from itertools import groupby
from dateutil.parser import isoparse


handler = Handler()


@handler.validate()
def validate(event) -> bool:
    url_secret = event['pathParameters'].get('secret', None)
    secret = SSM(with_decryption=True).get('jira_webhook_secret')
    return url_secret == secret


@handler.ingest()
def ingest(event) -> Data:
    body = loads(event['body'])
    event_type, item = body['event'], body['issue']

    @dataclass
    class JiraMetadata(Metadata):
        event_type: AnyStr = ''

    return Data(
        metadata=JiraMetadata(
            timestamp=datetime.now().timestamp(),
            event_type=event_type
        ),
        data={
            'issue': item['key'],
            'customer': item['fields']['labels'][0] if len(item['fields']['labels']) > 0 else '',
            'issue_status': item['fields']['status']['name'],
            'created': int(isoparse(item['fields']['created']).timestamp()),
            'updated': int(isoparse(item['fields']['updated']).timestamp())
        }
    )


@handler.process(partitions={
    'jira_issue_created': ['issue_status'],
    'jira_issue_updated': ['issue_status'],
})
def process(data) -> Dict[str, pd.DataFrame]:
    data = {
        k: [dict(x['data'], time=int(x['metadata']['timestamp'])) for x in v] for k, v in
        groupby([d.json() for d in data], key=lambda x: x['metadata']['event_type'])
    }

    return {
        'jira_issue_created': pd.DataFrame.from_records(data['created']) if 'created' in data else None,
        'jira_issue_updated': pd.DataFrame.from_records(data['updated']) if 'updated' in data else None
    }

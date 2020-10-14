from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
from json import loads
from typing import AnyStr
from dataclasses import dataclass
from dateutil.parser import isoparse


handler = IngestHandler()


@handler.validate()
def validate(event) -> bool:
    url_secret = event['pathParameters'].get('secret', None)
    secret = SSM(with_decryption=True).get('jira_webhook_secret')
    return url_secret == secret


@handler.ingest()
def ingest(event) -> Data:
    print(event)
    body = loads(event['body'])
    event_type, item = body['webhookEvent'].split(':')[-1], body['issue']

    @dataclass
    class JiraMetadata(Metadata):
        event_type: AnyStr

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

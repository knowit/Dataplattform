from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
from json import loads

handler = Handler()


@handler.validate()
def validate(event) -> bool:
    url_secret = event['pathParameters'].get('secret', None)
    secret = SSM(with_decryption=True).get('jira_webhook_secret')
    return url_secret == secret


@handler.ingest()
def ingest(event) -> Data:
    item = loads(event['body'])['issue']

    return Data(
        metadata=Metadata(
            timestamp=datetime.now().timestamp()
        ),
        data={
            'issue': item['key'],
            'customer': item['fields']['labels'][0] if len(item['fields']['labels']) > 0 else '',
            'issue_status': item['fields']['status']['name'],
            'created': item['fields']['created'],
            'updated': item['fields']['updated']
        }
    )


if __name__ == '__main__':
    # mock event
    handler({
        'pathParameters': {
            'secret': '12345'
        },
        'body': {
            'issue': {
                'key': 'TEST-1234',
                'fields': {
                    'created': '0000-00-00T00:00:00.000-0000',
                    'updated': '0000-00-00T00:00:00.000-0000',
                    'status': {'name': 'Open'},
                    'labels': ['Test Testerson'],
                }
            }
        }
    })

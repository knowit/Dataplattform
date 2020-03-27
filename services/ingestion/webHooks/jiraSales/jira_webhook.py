from dataplattform.common.handler import ingestion
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
from json import loads

handler = ingestion()


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

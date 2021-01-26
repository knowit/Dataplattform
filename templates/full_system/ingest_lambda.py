from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime


handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:
    timestamp_now = datetime.now().timestamp()
    d = [
        {
            'alias': 'olanor',
            'test': 'This is a test message',
            'id': 1,
            'time_precise': str(datetime.now().timestamp())
        },
        {
            'alias': 'karnor',
            'test': 'This is also a test message',
            'id': 2,
            'time_precise': str(datetime.now().timestamp())
        }
    ]

    d2 = Data(
        metadata=Metadata(timestamp=int(timestamp_now)),
        data=d)

    return d2

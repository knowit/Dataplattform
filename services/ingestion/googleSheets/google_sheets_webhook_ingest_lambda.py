from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import json

handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:

    event_body = event['body']
    body_json = json.loads(event_body)

    return Data(
        Metadata(timestamp=int(datetime.now().timestamp())),
        data=body_json
    )

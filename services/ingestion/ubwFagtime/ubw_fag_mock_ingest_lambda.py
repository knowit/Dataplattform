from dataplattform.common.handlers.ingest import IngestHandler
import json
from dataplattform.common.schema import Data, Metadata
from datetime import datetime

handler = IngestHandler()


@handler.ingest()
def mock(event) -> Data:
    test_data = open('tests/test_data.json')
    test_json = json.load(test_data)

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data=test_json['data']
    )

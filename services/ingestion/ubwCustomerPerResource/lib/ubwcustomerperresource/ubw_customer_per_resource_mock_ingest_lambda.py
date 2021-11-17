from dataplattform.common.handlers.ingest import IngestHandler
import json
from dataplattform.common.schema import Data, Metadata
from datetime import datetime

handler = IngestHandler()


@handler.ingest()
def mock(event) -> Data:
    with open('../../tests/test_data.json') as f:
        test_json = json.load(f)

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data=test_json['reg_period_2']
    )
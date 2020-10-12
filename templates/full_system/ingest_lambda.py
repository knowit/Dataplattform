from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common import rawStorage as rs

from datetime import datetime


handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:
    timestamp_now = datetime.now().timestamp()
    d = [{'test': 'This is a test message', 'id': 1, 'time_presice': str(datetime.now().timestamp())},
         {'test': 'This is also a test message', 'id': 2, 'time_presice': str(datetime.now().timestamp())}]

    d2 = Data(
        metadata=Metadata(timestamp=int(timestamp_now)),
        data=d)

    rs.write_to_private_bucket(d2)
    return d2

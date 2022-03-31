from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime

handler = IngestHandler()


@handler.ingest(overwrite=True)
def ingest(event) -> Data:
    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data={})

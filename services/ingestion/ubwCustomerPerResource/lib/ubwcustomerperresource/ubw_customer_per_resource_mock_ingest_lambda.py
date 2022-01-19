from dataplattform.common.handlers.ingest import IngestHandler
import json
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
from pathlib import Path

handler = IngestHandler()


@handler.ingest()
def mock(event) -> Data:
    test_data_path = Path(__file__).resolve().parent.parent.parent / Path('tests') / Path('test_data.json')
    with open(test_data_path) as f:
        test_json = json.load(f)
    
    def flatten(t):
        return [item for sublist in t for item in sublist]

    data = flatten(list(test_json.values())[1:-1])

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data=data
    )
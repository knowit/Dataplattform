from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
import requests

base_url = 'https://jn76t2rune.execute-api.eu-central-1.amazonaws.com/dev'

handler = IngestHandler()


@handler.ingest()
def handler(event) -> Data:
    api_token = SSM(with_decryption=True).get('API_KEY')
    res = requests.get(f'{base_url}/answers', headers={'x-api-key': api_token})
    print()
    print(api_token)
    print(res.status_code)
    print(res)

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data=res
    )

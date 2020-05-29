from dataplattform.common.handler import Handler, Response
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
from json import loads
from typing import Dict, AnyStr
import pandas as pd
from dataclasses import dataclass
import hmac
import hashlib
from dateutil.parser import isoparse

handler = Handler()


@handler.validate()
def validate(event) -> bool:
    def validate_signature(body, received_signature):
        """
        # Do something with a received signature (hand shake or comparison?)
        hash_type, signature = received_signature.split("=")
        if hash_type != "sha1":
            return False
        shared_secret = SSM(with_decryption=True).get('github_shared_secret')
        calculated_signature = hmac.new(shared_secret.encode(), body.encode(),
                                        hashlib.sha1).hexdigest()
        return hmac.compare_digest(calculated_signature, signature)
        """
        return True

    """
    headers = event["headers"]
    if "X-Hub-Signature" not in headers:
        return False
    """
    return True


@handler.ingest()
def ingest(event) -> Data:
    # TODO: What is the "body" of the event?

    item = loads(event["body"])
    info = item.get('TODO', None)
    
    def to_timestamp(date):
        return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

    return Data(
        metadata=GithubMetadata(
            timestamp=datetime.now().timestamp(),
            event=event['headers']['X-GSuite-Event']
        ),
        data_custom={
            'id': info['id']
            }
    )


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    records = [dict(x['data'], time=int(x['metadata']['timestamp'])) for x in [d.json() for d in data]]
    return {
        'custom_table_name': pd.DataFrame.from_records(records)
    }

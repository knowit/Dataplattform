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
        hash_type, signature = received_signature.split("=")
        if hash_type != "sha1":
            return False
        shared_secret = SSM(with_decryption=True).get('github_shared_secret')
        calculated_signature = hmac.new(shared_secret.encode(), body.encode(),
                                        hashlib.sha1).hexdigest()
        return hmac.compare_digest(calculated_signature, signature)

    headers = event["headers"]
    if "X-Hub-Signature" not in headers:
        return False

    return validate_signature(event["body"], headers["X-Hub-Signature"])


@handler.ingest()
def ingest(event) -> Data:
    item = loads(event["body"])
    repo = item.get('repository', None)
    if repo is None:
        return Response()

    @dataclass
    class GithubMetadata(Metadata):
        event: AnyStr

    return Data(
        metadata=GithubMetadata(
            timestamp=datetime.now().timestamp(),
            event=event['headers']['X-GitHub-Event']
        ),
        data={
            'id': repo['id'],
            'updated_at': int(isoparse(repo['updated_at']).timestamp()),
            'pushed_at': int(isoparse(repo['pushed_at']).timestamp()),
            'forks_count': repo['forks_count'],
            'stargazers_count': repo['stargazers_count']
        }
    )


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    records = [dict(x['data'], time=int(x['metadata']['timestamp'])) for x in [d.json() for d in data]]
    return {
        'github_knowit_repo_status': pd.DataFrame.from_records(records)
    }

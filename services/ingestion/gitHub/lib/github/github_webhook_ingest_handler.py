from dataplattform.common.handlers.ingest import IngestHandler, Response
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
from json import loads
from typing import AnyStr
from dataclasses import dataclass
import hmac
import hashlib
from dateutil.parser import isoparse

handler = IngestHandler()


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

    def to_timestamp(date):
        return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

    return Data(
        metadata=GithubMetadata(
            timestamp=datetime.now().timestamp(),
            event=event['headers']['X-GitHub-Event']
        ),
        data={
            'id': repo.get('id', ''),
            'name': repo.get('name', ''),
            'description': repo.get('description', ''),
            'url': repo.get('url', ''),
            'html_url': repo.get('html_url', ''),
            'owner': repo.get('owner', {}).get('login', ''),
            'created_at': to_timestamp(repo.get('created_at', '')),
            'updated_at': to_timestamp(repo.get('updated_at', '')),
            'pushed_at': to_timestamp(repo.get('pushed_at', '')),
            'language': repo.get('language', ''),
            'forks_count': repo.get('forks_count', ''),
            'stargazers_count': repo.get('stargazers_count', ''),
            'default_branch': repo.get('default_branch', '')
        }
    )

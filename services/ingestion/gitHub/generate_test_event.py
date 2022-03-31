import json 
import hmac
from hashlib import sha1
import os
# must be done before dataplattform.common.aws is imported
os.environ["AWS_XRAY_SDK_ENABLED"] = "false"
os.environ["STAGE"] = "dev"
os.environ["SERVICE"] = "github"
from dataplattform.common.aws import SSM

with open("tests/test_data/test_webhook_ingest_data.json") as f:
    body = json.load(f)

shared_secret = SSM(with_decryption=True).get('github_shared_secret')
signature = hmac.new(shared_secret.encode(), json.dumps(body).encode(), sha1).hexdigest()
headers = {
    'X-Hub-Signature': 'sha1=' + signature,
    'X-GitHub-Event': 'test'
}

data = {
    'headers': headers,
    'body': json.dumps(body)
}


with open("test_event.json", 'w') as f:
    json.dump(data, f, indent=2)
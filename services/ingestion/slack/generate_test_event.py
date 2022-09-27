import json
import os
from dataplattform.common.aws import SSM
from hmac import new
from hashlib import sha256

# must be done before dataplattform.common.aws is imported
os.environ["AWS_XRAY_SDK_ENABLED"] = "false"
os.environ["STAGE"] = "dev"
os.environ["SERVICE"] = "slackWebhook"


with open("tests/test_message_data.json") as f:
    body = json.dumps(json.load(f))

secret = SSM(with_decryption=True).get("slack_signing_secret")

signature = new(secret.encode(), f"v0:0:{body}".encode(), sha256).hexdigest()

data = {
    "headers": {
        "X-Slack-Signature": "v0=" + signature,
        "X-Slack-Request-Timestamp": 0
    },
    "body": body
}

with open("test_event.json", 'w') as f:
    json.dump(data, f, indent=2)

import json
import os
from dataplattform.common.aws import SSM
# must be done before dataplattform.common.aws is imported
os.environ["AWS_XRAY_SDK_ENABLED"] = "false"
os.environ["STAGE"] = "dev"
os.environ["SERVICE"] = "jiraSalesWebhook"


secret = SSM(with_decryption=True).get("jira_webhook_secret")

with open('tests/test_message.json') as f:
    body = json.load(f)

data = {
    "pathParameters": {
        "secret": secret
    },
    "body": json.dumps(body)
}

with open('test_event.json', 'w') as f:
    json.dump(data, f)

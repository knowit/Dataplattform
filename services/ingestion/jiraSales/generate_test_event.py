import json 
import os
from dataplattform.common.aws import SSM

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

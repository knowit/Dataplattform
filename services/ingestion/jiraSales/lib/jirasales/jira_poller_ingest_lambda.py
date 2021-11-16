from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
from dateutil.parser import isoparse
from requests.auth import HTTPBasicAuth
from requests import get, post, put
from os import environ

handler = IngestHandler()


def register_or_update_webhooks():
    stage = environ['STAGE']
    password, username, webhook_secret = SSM(
        with_decryption=True).get('jira_sales_password', 'jira_sales_username', 'jira_webhook_secret')

    webhook_url = SSM().get('jira_sales_webhook_url')

    webhook_name = f"{stage}-jiraSalesWebhook"

    webhooks = get(webhook_url, auth=HTTPBasicAuth(username, password)).json()
    webhook = next((x for x in webhooks if x['name'] == webhook_name), None)
    webhook_payload = {
        "name": webhook_name,
        "url": f"https://9fdzlk5wrk.execute-api.eu-central-1.amazonaws.com/{stage}/jira-sales-webhook/{webhook_secret}",
        "events": [
            "jira:issue_created",
            "jira:issue_updated"
        ],
        "filters": {
            "issue-related-events-section": "project = SALG and status != 'Rejected'"
        },
        "excludeBody": False
    }

    if webhook is None:
        res = post(webhook_url, auth=HTTPBasicAuth(username, password), json=webhook_payload)
    else:
        res = put(webhook['self'], auth=HTTPBasicAuth(username, password), json=webhook_payload)

    if res.status_code == 201 or res.status_code == 200:
        print(f'Webhook {"registered" if res.status_code == 201 else "updated"}')
    else:
        print('\n'.join([' '.join(x.values()) for x in res.json()['messages']]))


@handler.ingest()
def ingest(event) -> Data:
    register_or_update_webhooks()
    password, username = SSM(with_decryption=True).get('jira_sales_password', 'jira_sales_username')
    search_url = SSM(with_decryption=False).get('jira_sales_search_url')
    res = get(search_url, auth=HTTPBasicAuth(username, password), json={
            'jql': "project = SALG and status != 'Rejected'",
            'fields': 'labels, status, created, updated'
        })
    data = [
            {
                'issue': item['key'],
                'customer': item['fields']['labels'][0] if len(item['fields']['labels']) > 0 else '',
                'issue_status': item['fields']['status']['name'],
                'created': int(isoparse(item['fields']['created']).timestamp()),
                'updated': int(isoparse(item['fields']['updated']).timestamp())
            }
            for item in
            res.json().get('issues', [])
        ]

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()),
                data=data)

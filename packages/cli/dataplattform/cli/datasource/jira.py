from dataplattform.common.aws import SSM
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.handler import Handler
from requests import get, post, put
from requests.auth import HTTPBasicAuth
from datetime import datetime
from dateutil.parser import isoparse
import numpy as np
import pandas as pd
from os import environ


def register_or_update_webhooks(stage: str):
    password, username, webhook_secret = SSM(
        with_decryption=True,
        path=f'{stage}/jiraSalesWebhook'
    ).get('jira_sales_password', 'jira_sales_username', 'jira_webhook_secret')

    webhook_url = SSM(
        with_decryption=False,
        path=f'{stage}/jiraSalesWebhook'
    ).get('jira_sales_webhook_url')

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


def poll_old_data(stage: str):
    environ['STAGE'] = stage
    environ['SERVICE'] = 'jiraSalesWebhook'

    handler = Handler(
        access_path=f'data/level-2/jira/sales',
        bucket=f'{stage}-datalake-datalake')

    @handler.ingest()
    def ingest(event):
        password, username = SSM(
            with_decryption=True,
        ).get('jira_sales_password', 'jira_sales_username')

        search_url = SSM(
            with_decryption=False,
        ).get('jira_sales_search_url')

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

        return Data(
            metadata=Metadata(
                timestamp=datetime.now().timestamp()
            ),
            data=data
        )

    @handler.process(partitions={
        'jira_issue_created': ['issue_status'],
        'jira_issue_updated': ['issue_status'],
    })
    def process(data):
        data = [
            [dict(x, time=d['metadata']['timestamp']) for x in d['data']]
            for d in [d.json() for d in data]
        ]
        data = np.hstack(data)

        return {
            'jira_issue_created': pd.DataFrame.from_records(data),
            'jira_issue_updated': pd.DataFrame.from_records(data)
        }

    handler(None)


def setup(stage: str):
    register_or_update_webhooks(stage)
    poll_old_data(stage)

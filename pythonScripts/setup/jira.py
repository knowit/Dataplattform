from dataplattform.common.aws import SSM, S3
from dataplattform.common.schema import Data, Metadata
from requests import get, post
from requests.auth import HTTPBasicAuth
from datetime import datetime


def register_or_update_webhooks(stage: str):
    password, username = SSM(
        with_decryption=True,
        path=f'{stage}/jiraSalesWebhook'
    ).get('jira_sales_password', 'jira_sales_username')

    webhook_url = SSM(
        with_decryption=False,
        path=f'{stage}/jiraSalesWebhook'
    ).get('jira_sales_webhook_url')

    res = post(webhook_url, auth=HTTPBasicAuth(username, password), json={
        "name": f"{stage}-jiraSalesWebhook",
        "url": f"https://9fdzlk5wrk.execute-api.eu-central-1.amazonaws.com/{stage}/jira-sales-webhook",
        "events": [
            "jira:issue_created",
            "jira:issue_updated"
        ],
        "filters": {
            "issue-related-events-section": "project = SALG and status != 'Rejected'"
        },
        "excludeBody": False
    })

    if res.status_code == 200:
        print('Webhook registered')
    else:
        print('\n'.join([' '.join(x.values()) for x in res.json()['messages']]))


def poll_old_data(stage: str):
    password, username = SSM(
        with_decryption=True,
        path=f'{stage}/jiraSalesWebhook'
    ).get('jira_sales_password', 'jira_sales_username')

    search_url = SSM(
        with_decryption=False,
        path=f'{stage}/jiraSalesWebhook'
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
            'created': item['fields']['created'],
            'updated': item['fields']['updated']
        }
        for item in
        res.json().get('issues', [])
    ]

    S3(
        access_path=f'data/level-2/jira/sales/',
        bucket=f'{stage}-datalake-datalake'  # queryable?
    ).put(
        Data(
            metadata=Metadata(
                timestamp=datetime.now().timestamp()
            ),
            data=data
        )
    )

    print(f'Uploaded {len(data)} old issues to {stage} S3 bucket')


def setup(stage: str):
    register_or_update_webhooks(stage)
    poll_old_data(stage)

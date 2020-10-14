from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
import pandas as pd
from itertools import groupby


handler = ProcessHandler()


@handler.process(partitions={
    'jira_issue_created': ['issue_status'],
    'jira_issue_updated': ['issue_status'],
})
def process(data, events) -> Dict[str, pd.DataFrame]:
    data = {
        k: [dict(x['data'], time=int(x['metadata']['timestamp'])) for x in v] for k, v in
        groupby([d.json() for d in data], key=lambda x: x['metadata']['event_type'])
    }

    return {
        'jira_issue_created': pd.DataFrame.from_records(data['issue_created']) if 'issue_created' in data else None,
        'jira_issue_updated': pd.DataFrame.from_records(data['issue_updated']) if 'issue_updated' in data else None
    }

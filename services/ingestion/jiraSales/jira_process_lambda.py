from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
import pandas as pd

handler = ProcessHandler()


@handler.process(partitions={
    'jira_issue_created': ['issue_status'],
    'jira_issue_updated': ['issue_status'],
})
def process(data, events) -> Dict[str, pd.DataFrame]:

    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        issues_dataframe = pd.json_normalize(payload)
        issues_dataframe['time'] = int(metadata['timestamp'])
        issues_dataframe['event_type'] = metadata.get('event_type', 'both')
        return issues_dataframe
    output_dataframe = pd.concat([make_dataframe(d) for d in data])
    issues_created = output_dataframe.loc[output_dataframe['event_type'] == 'issue_created'].copy()
    issues_updated = output_dataframe.loc[output_dataframe['event_type'] == 'issue_updated'].copy()
    issues_both = output_dataframe.loc[output_dataframe['event_type'] == 'both'].copy()

    return {
        'jira_issue_created': pd.concat([issues_created, issues_both]).drop(columns=['event_type']),
        'jira_issue_updated': pd.concat([issues_updated, issues_both]).drop(columns=['event_type'])
    }

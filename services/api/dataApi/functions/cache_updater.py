import json
from common_lib.common.repositories.reports import ReportsRepository
from common_lib.common.services.athena_engine import execute as execute_query
import common_lib.common.services.cache_table_service as cache_table_service


def handler(event, context):
    records = event['Records']

    def load_message(record):
        rec = record.get('Sns')
        return (rec.get('Subject', None), rec.get('Message', None))

    messages = [(topic, json.loads(msg)) for topic, msg in [
        load_message(record) for record in records
    ] if topic]

    def load_reports(topic: str, message, repo: ReportsRepository):
        if topic == 'NewReport':
            return [repo.get(message['report'])]
        elif topic == 'DataUpdate':
            return [report for table in message['tables'] for report in repo.get_by_tables(table)]

    with ReportsRepository() as repo:
        report_sets = [load_reports(topic, message, repo)
                       for topic, message in messages]
    reports = [report for reports in report_sets for report in reports]
    for report in reports:
        updateCache = cache_table_service.cache_table(
            report['dataProtection'], report['name'])
        updateCache(
            execute_query(report['queryString'],
                          protection_level=report['dataProtection'],
                          preprocess_sql=False)
        )

        with ReportsRepository() as repo:
            repo.update_cache_time(report['name'])

    return {}

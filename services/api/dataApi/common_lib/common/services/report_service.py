from common.repositories.reports import ReportsRepository
from dataplattform.common.aws import SNS
from common.services.athena_engine import process_sql
from typing import Dict
from functools import reduce
import re
import json
from os import environ


def pub_new_report(report: str):
    sns = SNS(environ.get('NEW_REPORT_TOPIC'))
    sns.publish(json.dumps({'report': report}), 'NewReport')


def new_report(new_report: Dict[str, str]):
    sql, used_tables = process_sql(new_report['queryString'])

    tables = [table for (database, table) in used_tables]
    data_protection_level = reduce(
        lambda x, y: x if x >= y else y,
        [
            int(next(iter(re.findall(r'\d', database))))
            for (database, table) in used_tables
        ], 3
    )

    with ReportsRepository() as repo:
        repo.create({
            'name': new_report['name'],
            'queryString': sql,
            'tables': tables,
            'dataProtection': data_protection_level
        })
        pub_new_report(new_report['name'])
        return repo.get(new_report['name'])

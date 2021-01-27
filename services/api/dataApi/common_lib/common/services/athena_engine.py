import boto3
from botocore.exceptions import ClientError
import sqlparse
from time import sleep
import pandas as pd
from io import BytesIO
from os import environ
from cachetools import cached, TTLCache
from typing import Tuple, List
from dataplattform.common.aws import S3


@cached(cache=TTLCache(1, 60))
def table_map():
    athena = boto3.client('athena')

    list_catalogs = athena.get_paginator('list_data_catalogs')
    list_databases = athena.get_paginator('list_databases')
    list_tables = athena.get_paginator('list_table_metadata')

    try:
        return [
            (catalog, db, table['Name'])
            for (catalog, db) in [
                (catalog, db['Name'])
                for catalog in [
                    catalog['CatalogName']
                    for resp in list_catalogs.paginate()
                    for catalog in resp['DataCatalogsSummary']
                ]
                for resp in list_databases.paginate(CatalogName=catalog)
                for db in resp['DatabaseList']
            ]
            for resp in list_tables.paginate(CatalogName=catalog, DatabaseName=db)
            for table in resp['TableMetadataList']
        ]

    except ClientError as error:
        raise Exception(error.response['Error']['Message'])


def process_sql(sql: str) -> Tuple[str, List[Tuple[str, str]]]:
    used_tables = []
    for (_, database, table) in table_map():
        if table in sql:
            used_tables.append((database, table))
            sql = sql.replace(table, f'{database}.{table}')

    statement = sqlparse.parse(sql)[0]
    if statement.get_type() != 'SELECT':
        raise Exception('Illegal SQL statement')

    return str(statement), used_tables


def query_complete(athena, query_id: str):
    response = athena.get_query_execution(QueryExecutionId=query_id)
    status = response['QueryExecution']['Status']['State']
    if status == 'SUCCEEDED':
        return response['QueryExecution']['ResultConfiguration']['OutputLocation']
    elif status == 'FAILED' or status == 'CANCELLED':
        raise Exception(f'Athena exection failed: {response["QueryExecution"]["Status"]["StateChangeReason"]}')
    else:
        return None


def execute(sql: str, preprocess_sql=True) -> pd.DataFrame:
    if preprocess_sql:
        sql, _ = process_sql(sql)

    s3 = boto3.resource('s3')
    athena = boto3.client('athena')

    begin_query_response = athena.start_query_execution(
        QueryString=sql,
        ResultConfiguration={
            'OutputLocation': f's3://{environ.get("DATALAKE", "dev-datalake-datalake")}/query/',
            'EncryptionConfiguration': {'EncryptionOption': 'SSE_S3'}
        }
    )

    query_id = begin_query_response['QueryExecutionId']

    while True:
        sleep(0.1)
        output_location = query_complete(athena, query_id)
        if output_location is not None:
            break

    bucket, *path = output_location.lstrip('s3://').split('/')
    data = s3.Object(bucket, '/'.join(path)).get()

    s3 = S3(access_path='', bucket=bucket)
    s3.empty_content_in_path("query")

    # TODO store in s3 and return presigned download url
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html

    return pd.read_csv(BytesIO(data['Body'].read()))

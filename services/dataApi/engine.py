import boto3
import sqlparse
from time import sleep
import pandas as pd
from io import BytesIO
from os import environ


def query_complete(athena, query_id: str):
    response = athena.get_query_execution(QueryExecutionId=query_id)
    status = response['QueryExecution']['Status']['State']
    if status == 'SUCCEEDED':
        return response['QueryExecution']['ResultConfiguration']['OutputLocation']
    elif status == 'FAILED' or status == 'CANCELLED':
        raise Exception('Athena exection failed')
    else:
        return None


def execute(sql: str, output_format: str):
    statement = sqlparse.parse(sql)[0]
    if statement.get_type() != 'SELECT':
        raise Exception('Illegal SQL statement')

    if output_format not in ['json', 'csv']:
        raise Exception('Unknown output format')

    s3 = boto3.resource('s3')
    athena = boto3.client('athena')

    begin_query_response = athena.start_query_execution(
        QueryString=str(statement),
        ResultConfiguration={
            'OutputLocation': f's3://{environ.get("DATALAKE")}/query/',
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

    df = pd.read_csv(BytesIO(data['Body'].read()))

    if output_format == 'json':
        return df.to_json(orient='records')
    elif output_format == 'csv':
        return df.to_csv(index=False)

    return None

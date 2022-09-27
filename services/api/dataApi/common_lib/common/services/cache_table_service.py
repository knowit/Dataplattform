import boto3
from os import environ, remove
from tempfile import mkstemp
from typing import Tuple, List


def cached_key(protection: int, name: str) -> Tuple[str, str]:
    return (
        environ.get("DATALAKE", "dev-datalake-bucket"),
        f'reports/level-{protection}/{name}.gzip'
    )


def cached_object(protection: int, name: str):
    bucket, key = cached_key(protection, name)
    s3 = boto3.resource('s3')
    return s3.Object(bucket, key)


def query_cache_table(protection: int, name: str):
    bucket, key = cached_key(protection, name)
    client = boto3.client('s3')

    def query(filters: List[Tuple[str, str]]):
        filter_str = 'where ' + ' '.join([
            f's.{key} = {value}' for (key, value) in filters
        ]) if filters and len(filters) > 0 else ''

        response = client.select_object_content(
            Bucket=bucket,
            Key=key,
            ExpressionType='SQL',
            Expression=f'select * from s3object s {filter_str}',
            InputSerialization={'Parquet': {}},
            OutputSerialization={
                'JSON': {'RecordDelimiter': ','}
            }
        )
        records = b''.join([
            payload['Records']['Payload']
            for payload in response['Payload']
            if 'Records' in payload
        ]).decode('utf-8').rstrip(',')
        return f'[{records}]'

    return query


def delete_cache_table(protection: int, name: str):
    cached_object(protection, name).delete()
    return True


def cache_table(protection: int, name: str):
    cache_object = cached_object(protection, name)

    def set_cache(dataframe):
        _, filename = mkstemp()
        dataframe.to_parquet(
            filename,
            engine='fastparquet',
            compression='GZIP',
            index=False)
        with open(filename, 'rb') as f:
            return cache_object.put(Body=f)
        remove(filename)

    return set_cache

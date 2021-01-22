import boto3
from os import environ
from dataplattform.common.repositories.person_repository import PersonRepository


def get_guids():
    with PersonRepository() as repo:
        return repo.get_guids()


def check_partitionkeys(table):
    for pk in table['PartitionKeys']:
        if pk['Name'] == 'guid':
            return True
    return False


def transform_uri(uri, bucketname):
    print(bucketname)
    prefix = f's3://{bucketname}/'
    return uri[len(prefix):]


def handler(event, context):
    glue = boto3.client('glue')
    datalake = boto3.resource('s3').Bucket(environ.get('DATALAKE'))
    guids = get_guids()

    for database in glue.get_databases()['DatabaseList']:
        tables = glue.get_tables(DatabaseName=database['Name'])
        tables = filter(check_partitionkeys, tables['TableList'])
        for table in tables:
            outdated_partitions = glue.get_partitions(
                DatabaseName=database['Name'],
                TableName=table['Name'],
                Expression="guid NOT IN ({})".format(','.join(map(lambda g: f"'{g}'", guids)))
            )['Partitions']

            partitions_to_delete = [{k: v for k, v in p.items() if k == 'Values'} for p in outdated_partitions]

            glue.batch_delete_partition(
                DatabaseName=database['Name'],
                TableName=table['Name'],
                PartitionsToDelete=partitions_to_delete
            )

            for p in outdated_partitions:
                keyPrefix = transform_uri(p['StorageDescriptor']['Location'], datalake.name)
                print(keyPrefix)
                datalake.objects.filter(Prefix=keyPrefix).delete()

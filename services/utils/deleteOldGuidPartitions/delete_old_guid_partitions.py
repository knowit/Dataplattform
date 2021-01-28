from os import environ
from dataplattform.common.repositories.person_repository import PersonRepository
from dataplattform.common.helper import empty_content_in_path
from dataplattform.common.aws import Glue


def get_guids():
    with PersonRepository() as repo:
        return repo.get_guids()


def check_partitionkeys(table):
    for pk in table['PartitionKeys']:
        if pk['Name'] == 'guid':
            return True
    return False


def transform_uri(uri, bucketname):
    prefix = f's3://{bucketname}/'
    return uri[len(prefix):]


def handler(event, context):
    glue = Glue()
    guids = get_guids()

    for database in glue.get_databases():
        tables = glue.get_tables(database['Name'])
        tables = filter(check_partitionkeys, tables)
        for table in tables:
            partitions_to_delete = glue.get_partitions(
                database['Name'],
                table['Name'],
                "guid NOT IN ({})".format(','.join(map(lambda g: f"'{g}'", guids)))
            )

            values = [{k: v for k, v in p.items() if k == 'Values'} for p in partitions_to_delete]

            glue.delete_partitions(database['Name'], table['Name'], values)

            datalake = environ.get("DATALAKE")
            for p in partitions_to_delete:
                keyPrefix = transform_uri(p['StorageDescriptor']['Location'], datalake)
                empty_content_in_path(environ.get('DATALAKE'), keyPrefix)

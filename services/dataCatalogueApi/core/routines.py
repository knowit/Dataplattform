import botocore
import boto3
ignore_databases = ['default']


def to_lower_case(d_list):
    return [dict((k.lower(), v) for k, v in d.items()) for d in d_list]


def get_all_valid_databases(glue_client):

    paginator = glue_client.get_paginator('get_databases')
    response_iterator = paginator.paginate()
    db_list = []
    for database_lists in response_iterator:
        for db in database_lists['DatabaseList']:
            db_list.append(db)

    db_list = [db for db in db_list if db['Name'] not in ignore_databases]
    return db_list


def get_valid_database(api, glue_client, database_name):
    if database_name not in ignore_databases:
        try:
            db = glue_client.get_database(Name=database_name)
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'EntityNotFoundException':
                api.abort(404, 'Database ' + database_name + ' not found')
            else:
                raise error
        return db
    else:
        api.abort(404, 'Database ' + database_name + ' not found')


def get_tables(api, glue_client, database_name):
    paginator = glue_client.get_paginator('get_tables')
    if database_name not in ignore_databases:
        try:
            response_iterator = paginator.paginate(DatabaseName=database_name)
            db_tables = []
            for tables in response_iterator:
                for table in tables['TableList']:
                    db_tables.append(table)
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'EntityNotFoundException':
                api.abort(404, 'Database ' + database_name + ' not found')
            else:
                raise error
        return db_tables
    else:
        api.abort(404, 'Database ' + database_name + ' not found')


def get_all_tables(api):
    glue_client = boto3.client('glue')
    dbs_list = get_all_valid_databases(glue_client)
    tables = []
    for db in dbs_list:
        db_tables = get_tables(api, glue_client, db['Name'])
        for table in db_tables:
            tables.append(table['Name'])
    return tables


def get_all_databases(api):
    glue_client = boto3.client('glue')
    dbs_list = get_all_valid_databases(glue_client)
    databases = [get_database_content(api, db['Name']) for db in dbs_list]
    return databases


def get_database_content(api, database_name):
    glue_client = boto3.client('glue')
    db = get_valid_database(api, glue_client, database_name)
    db_tables = get_tables(api, glue_client, database_name)
    db_table_names = [table['Name'] for table in db_tables]
    data = {}
    data['name'] = db.get('Database', {}).get('Name')
    data['createTime'] = db.get('Database', {}).get('CreateTime')
    data['tables'] = db_table_names
    return data


def get_table(api, database_name, table_name):
    glue_client = boto3.client('glue')
    if database_name not in ignore_databases:
        try:
            table_response = glue_client.get_table(DatabaseName=database_name, Name=table_name)
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'EntityNotFoundException':
                api.abort(404, error.response['Error']['Message'])
            else:
                raise error

        table = table_response.get('Table', {})
        data = {'name': table_name,
                'databaseName': table.get('DatabaseName', ''),
                'createTime': table.get('CreateTime'),
                'updateTime': table.get('UpdateTime'),
                'lastAccessTime': table.get('LastAccessTime'),
                'columns': to_lower_case(table.get('StorageDescriptor', {}).get('Columns')),
                'partitionKeys': to_lower_case(table.get('PartitionKeys', []))
                }
        return data
    else:
        api.abort(404, 'Database ' + database_name + ' not found')


def get_database_from_tablename(api, table_name):
    dbs = get_all_databases(api)
    for db in dbs:
        if table_name in db['tables']:
            return db['name']
    api.abort(404, 'Table ' + table_name + ' not found')


def get_single_table(api, table_name):
    return get_table(api, get_database_from_tablename(api, table_name), table_name)

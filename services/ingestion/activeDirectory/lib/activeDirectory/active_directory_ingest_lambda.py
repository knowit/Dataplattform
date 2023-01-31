import requests
import pandas as pd
import boto3
from os import environ
import json
import hashlib

url = 'http://10.205.0.5:20201/api/Users'


def handler(event, context):
    res = requests.get(f'{url}')
    data_json = res.json()

    def get_list_of_users(data):
        list_of_users = []
        for user in data:
            user_details = user['userDetails']
            list_of_users.append(user_details)
        return list_of_users

    users = get_list_of_users(data_json)

    def make_dataframe(d):
        df = pd.json_normalize(d)
        m = hashlib.sha1()
        m.update(df['samAccountName'][0].encode('utf-8'))
        df['guid'] = m.hexdigest()
        return df

    df = pd.concat([make_dataframe(d) for d in users], ignore_index=True)
    df = df.loc[~df['isServiceUser'], :]
    df = df.loc[~df['isExternalUser'], :]
    df = df.loc[~df['isDeleted'], :]

    employee_table = [
        'guid',
        'primaryEmailAddress',
        'displayName',
        'samAccountName',
        'company',
        'knowitBranch',
        'distinguishedName',
        'managerDistinguishedName',
        'manager.primaryEmailAddress',
    ]

    employee_df = df[employee_table].copy()
    employee_df.rename(columns={
        'primaryEmailAddress': 'email',
        'samAccountName': 'alias',
        'distinguishedName': 'distinguished_name',
        'manager.primaryEmailAddress': 'manager_email',
        'managerDistinguishedName': 'manager'
        }, inplace=True)
    employee_df = employee_df.fillna("")

    employee_df['manager'] = employee_df['manager'].str.split('=').str[1].str.split(',').str[0]
    employee_df['distinguished_name'] = employee_df['distinguished_name'].str.split('=').str[1].str.split(',').str[0]

    for i in employee_df.columns:
        employee_df[i] = employee_df[i].astype(str)

    resource = boto3.resource('dynamodb')
    table = resource.Table(environ.get('PERSON_DATA_TABLE'))
    df_json = json.loads(json.dumps(employee_df.to_dict(orient='records')))

    with table.batch_writer() as batch:
        for each in table.scan()['Items']:
            batch.delete_item(
                Key={
                    'guid': each['guid'],
                }
            )

    with table.batch_writer() as batch:
        for element in df_json:
            batch.put_item(Item=element)

    return 200

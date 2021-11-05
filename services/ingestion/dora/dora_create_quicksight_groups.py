import boto3
import pandas as pd

quicksight_client = boto3.client('quicksight')
glue_client = boto3.client('glue')
sts_client = boto3.client('sts')
s3_client = boto3.client('s3')
s3 = boto3.resource('s3')

role_bindings_filename = 'quicksight_role_bindings.csv'


def handler(event, context):
    account_id = sts_client.get_caller_identity().get('Account')
    s3_bucket = s3.Bucket(f'dev-datalake-bucket-{account_id}')

    def create_quicksight_group(partition):
        return quicksight_client.create_group(
            GroupName=partition,
            Description=f'Group that gives access to {partition} key metrics',
            AwsAccountId=account_id,
            Namespace='default'
        )

    def update_role_bindings(groups):
        data_frame = pd.DataFrame({
            'Group': groups,
            'partition_1': groups
        })

        data_frame.to_csv(f'/tmp/{role_bindings_filename}', mode='w+', index=False, header=True)
        s3_bucket.upload_file(f'/tmp/{role_bindings_filename}', role_bindings_filename)

    quicksight_groups = quicksight_client.list_groups(
        AwsAccountId=account_id,
        MaxResults=100,
        Namespace='default'
    )

    quicksight_group_names = [group['GroupName'] for group in quicksight_groups['GroupList']]
    partitions = glue_client.get_partitions(DatabaseName='dev_level_4_database', TableName='github_dora_repos')
    partition_names = ['/'.join(partition['Values']) for partition in partitions['Partitions']]

    created_groups = \
        [create_quicksight_group(partition) for partition in partition_names if partition not in quicksight_group_names]

    update_role_bindings(partitions)

    return {
        'message': 'success!'
    }

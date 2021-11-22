import boto3

glue_client = boto3.client('glue')
athena_client = boto3.client('athena')


def handler(event, context):
    print('## TRIGGERED BY EVENT: ')
    print(event)
    partitions_created = event['detail']['partitionsCreated']
    # If not 0, new repo has been added -> initiate view creation

    # Need to find which new repo has been added
    # Check last partitions created
    # SELECT * FROM dora_repos WHERE partition_col LIKE
    partitions_response = glue_client.get_partitions(DatabaseName='dev_level_4_database', TableName='github_dora_repos')
    partitions = sorted(partitions_response['Partitions'], key=lambda k: k['CreationTime'])

    print(partitions)

    print(partitions[0]['CreationTime'])

    latest_partition = partitions[0]
    repo_name = "-".join(latest_partition['Values'])



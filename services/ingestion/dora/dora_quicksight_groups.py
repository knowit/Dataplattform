import boto3

quicksight_client = boto3.client('quicksight')
glue_client = boto3.client('glue')
sts_client = boto3.client('sts')

def handler(event, context):

    account_response = str(sts_client.get_caller_identity()['Account'])

    partitions_response = glue_client.get_partitions(DatabaseName='dev_level_4_database', TableName='github_dora_repos')
    partitions = sorted(partitions_response['Partitions'], key=lambda k: k['CreationTime'])

    response_groups = quicksight_client.list_groups(
        AwsAccountId = account_response,
        MaxResults = 100,
        Namespace = 'default'
    )


    def get_group_names(response):
        list_of_groups = []
        for group in response:
            list_of_groups.append(group['GroupName'])
        return list_of_groups

    def create_groups(existing_groups):
        for partition in partitions[0]['Values']:
            if(partition not in existing_groups):
                quicksight_client.create_group(
                    GroupName = partition,
                    Description = 'Group for people working in the project', #fix
                    AwsAccountId = account_response,
                    Namespace = 'default'
                )

    create_groups(get_group_names(response_groups['GroupList']))

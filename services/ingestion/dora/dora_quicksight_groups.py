import boto3
import csv

quicksight_client = boto3.client('quicksight')
glue_client = boto3.client('glue')
sts_client = boto3.client('sts')
s3 = boto3.resource('s3')
bucket = s3.Bucket('BUCKET_NAME')

key = 'KEY_PATH'

def handler(event, context):

    account_response = str(sts_client.get_caller_identity()['Account'])

    partitions_response = glue_client.get_partitions(DatabaseName='dev_level_4_database', TableName='github_dora_repos')
    partitions = sorted(partitions_response['Partitions'], key=lambda k: k['CreationTime'])

    response_groups = quicksight_client.list_groups(
        AwsAccountId = account_response,
        MaxResults = 100,
        Namespace = 'default'
    )

    def get_existing_groups(groups):
        list_of_groups = []
        for group in groups['GroupList']:
            list_of_groups.append(group['GroupName'])
        return list_of_groups


    def get_group_names(response, existing_groups):
        list_of_groups = []
        for group in response:
            if(group not in existing_groups):
                list_of_groups.append(group)
        return list_of_groups

    def get_new_groups():
        list_of_existing_groups = []
        for partition in partitions[0]['Values']:
            list_of_existing_groups.append(partition)
        return list_of_existing_groups


    def create_groups(partitions):
        for partition in partitions:
            quicksight_client.create_group(
                GroupName = partition,
                Description = 'Group for people working in the project', #fix
                AwsAccountId = account_response,
                Namespace = 'default'
            )

    def update_rolebinding(rolebindings):
        local_file_name = '/tmp/rolebinding.csv'
        s3.Bucket('BUCKET_NAME').download_file(key, local_file_name)

        new_rolebindings = rolebindings

        with open('tmp/rolebinding.csv', 'r') as infile:
            reader = list(csv.reader(infile))
            reader.insert(0,new_rolebindings)

        with open('tmp/rolebindings.csv', 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            for line in reader:
                writer.writerow(line)

        bucket.upload_file('/tmp/rolebindings.csv', key)

    glue_groups = get_new_groups()
    existing_group = get_existing_groups(response_groups)
    new_groups = get_group_names(glue_groups, existing_group)
    create_groups(new_groups)
    #update_rolebinding(new_groups)

    return {
        'message': 'success!'
    }

import boto3
import botocore
import pandas as pd
import io

quicksight_client = boto3.client('quicksight')
glue_client = boto3.client('glue')
sts_client = boto3.client('sts')
s3_client = boto3.client('s3')
s3 = boto3.resource('s3')
bucket = s3.Bucket('dev-datalake-bucket-876363704293')

key = 'quicksight-rolebindings.csv'

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

    def download_csv_to_temp(filename, bucketname):
        local_file_name = '/tmp/rolebinding.csv'
        s3.Bucket(bucketname).download_file(key, local_file_name)

    def read_rolebindings(filename, bucketname):
        csv_obj = s3_client.get_object(Bucket=bucketname, Key=filename)
        csv_string = csv_obj['Body'].read().decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_string))
        list_of_roles = []
        for roles in df.Role:
            list_of_roles.append(roles)
        return list_of_roles

    def write_to_csv(dataframes, filename):
        df = pd.concat(dataframes)
        df.to_csv('/tmp/' + filename + '.csv', mode = 'a', index = False, header = True)

    def add_to_dataframe(group):
        df = pd.DataFrame({
            'Group': [group],
            'partition_1': [group]
        })
        return df

    def update_rolebinding(filename, bucketname):
        existing_group = get_existing_groups(response_groups)
        download_csv_to_temp(filename, bucketname)
        existing_rolebindings = read_rolebindings(filename, bucketname)

        list_of_df = []
        for group in existing_group:
            if group not in existing_rolebindings:
                list_of_df.append(add_to_dataframe(group))
        
        write_to_csv(list_of_df, filename)

        bucket.upload_file('/tmp/' + filename + '.csv', key)

    glue_groups = get_new_groups()
    existing_group = get_existing_groups(response_groups)
    new_groups = get_group_names(glue_groups, existing_group)
    create_groups(new_groups)
    update_rolebinding("quicksight-rolebindings.csv", 'dev-datalake-bucket-876363704293')

    return {
        'message': 'success!'
    }

import boto3
import pandas as pd
import io

quicksight_client = boto3.client('quicksight')
sts_client = boto3.client('sts')
account_response = str(sts_client.get_caller_identity()['Account'])
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

csv = "quicksight-users.csv"
bucket = 'dev-datalake-bucket-876363704293'
namespace = 'default'


def handler(event, context):

    def list_users():
        users = quicksight_client.list_users(
            AwsAccountId = account_response,
            Namespace = 'default'
        )
        list_of_users = []
        for user in users['UserList']:
            list_of_users.append(user['UserName'])
        return list_of_users

    def add_membership(name, group):
        quicksight_client.create_group_membership(
            MemberName = name,
            GroupName = group,
            AwsAccountId = account_response,
            Namespace = 'default'
        )

    def add_user(name, email):
        quicksight_client.register_user(
            IdentityType = 'QUICKSIGHT',
            Email = email,
            UserRole = 'READER',
            AwsAccountId = account_response,
            Namespace = namespace,
            UserName = name,
        )

    def get_members(filename, bucketname):
        csv_obj = s3_client.get_object(Bucket=bucketname, Key=filename)
        csv_string = csv_obj['Body'].read().decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_string))
        list_of_users = []
        for i in df.itertuples():
            member_info = []
            member_info.append(i.User)
            member_info.append(i.Email)
            member_info.append(i.Group)
            list_of_users.append(member_info)
        return list_of_users

    def delete_membership(member, groups):
        for group in groups:
            quicksight_client.delete_group_membership(
                MemberName = member,
                GroupName = group,
                AwsAccountId = account_response,
                Namespace = namespace
            )
    
    def delete_user(user):
        quicksight_client.delete_user(
            UserName = user,
            AwsAccountId = account_response,
            Namespace = namespace
        )

    def get_memberships(user):
        membership = quicksight_client.list_user_groups(
            UserName = user,
            AwsAccountId = account_response,
            Namespace = namespace
        )
        list_of_memberships = [item['GroupName'] for item in membership['GroupList']]
        return list_of_memberships

    def create_quicksight_users():
        members = get_members(csv, bucket)
        users = list_users()
        for member in members:
            if(member[0] not in users):
                try:
                    add_user(member[0],member[1])
                except:
                    continue
                add_membership(member[1],member[2])
        member_names = [item[0] for item in members]
        for user in users:
            if user not in member_names:
                delete_membership(user, get_memberships(user))
                delete_user(user)

    create_quicksight_users()
    return {
        'message': 'success!'
    }
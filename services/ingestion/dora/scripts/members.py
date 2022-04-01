import argparse
import boto3
import pandas as pd

s3_client = boto3.client('s3')
sts_client = boto3.client('sts')
account_response = str(sts_client.get_caller_identity()['Account'])  # Gets correct id from the user account
bucket = f"datalake-bucket-{account_response}"
file = "data/level-3/dora/dora_users.csv"


# Adds a member to the list
def add_member(args):
    user_name = args.name
    user_email = args.email
    group_name = args.group

    s3_df = get_file()
    user_row = s3_df.loc[s3_df['UserName'] == user_name]

    if user_row.empty:
        member = pd.DataFrame({'UserName': [user_name], 'Email': [user_email], 'Group': [group_name]})
        s3_df = s3_df.append(member)
        write_to_s3(s3_df)
        return

    print(user_row['Group'])

    print(s3_df)


# Removes a member from the list
def remove_member(args):
    member = args.member

    df = get_file()

    if member in df['UserName'].values:
        df = df[df['UserName'] != member]
        write_to_s3(df)
        print(f'User {member} removed from lists')
    else:
        print(f"{member} is not a member")


# Retrieves and list all members ( This method might need revisiting if the membership expands)
def get_members():
    data = get_file()
    print(data)


# Get the correct stage, only handles dev and prod
def get_stage(bucket):
    session = boto3.session.Session()
    s3_resource = session.resource('s3')
    if (s3_resource.meta.client.head_bucket(Bucket=f"dev-{bucket}")):
        return "dev-"
    elif (s3_resource.meta.client.head_bucket(Bucket=f"prod-{bucket}")):
        return "prod-"
    else:
        return False


# Retrieve file from S3 and create a dataframe
def get_file():
    staged_bucket = f"{get_stage(bucket)}{bucket}"
    s3_object = s3_client.get_object(Bucket=staged_bucket, Key=file)
    s3_df = pd.read_csv(s3_object.get("Body"))
    return s3_df


# Saves data directly to s3 bucket
def write_to_s3(data):
    data.to_csv(f's3://{get_stage(bucket)}{bucket}/{file}', index=False)


# Create a parser that takes CLI cmds and requires the use of the subparser
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='cmd', required=True)

# Create subparsers
add_member_parser = subparsers.add_parser('add', help='Add a member to quicksight')
remove_member_parser = subparsers.add_parser('remove', help='Remove a member from quicksight')
get_members_parser = subparsers.add_parser('get', help='Lists quicksight members')

# Add arguments for the subparsers
add_member_parser.add_argument("--name", help="Members username", required=True)
add_member_parser.add_argument("--email", help="Members email address", required=True)
add_member_parser.add_argument("--group", help="The groups the person is a member of", required=True)

remove_member_parser.add_argument("--member", help="Username of the member", required=True)

# Set functions for the subparsers
get_members_parser.set_defaults(func=get_members)
add_member_parser.set_defaults(func=add_member)
remove_member_parser.set_defaults(func=remove_member)


def main():
    args = parser.parse_args()
    try:  # Without this the get command fails as it has 0 args
        args.func(args)
    except:
        args.func()


if __name__ == "__main__":
    main()

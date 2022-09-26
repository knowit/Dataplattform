import argparse
import boto3
import pandas as pd

s3_client = boto3.client('s3')
sts_client = boto3.client('sts')
account_response = str(sts_client.get_caller_identity()['Account']) #Gets correct id from the user account
bucket = f"datalake-bucket-{account_response}"
file = "data/level-3/dora/dora_users.csv"

# Adds a member to the list
def add_member(user_name,email,group_name):
    s3_df = get_file()
    if s3_df['Names'].str.contains(user_name).any():
        print (f"{user_name} is already a member")
    else:
        members = {'UserName':[user_name], 'Email':[email], 'GroupName': [group_name]}
        df = pd.DataFrame(members)
        s3_df = s3_df.append(df)
        write_to_s3(s3_df, bucket, file)

# Removes a member from the list
def remove_member(member):
    df = get_file()
    if df['Names'].str.contains(member).any():
        df = df[df.UserName != member]
        write_to_s3(df)
    else:
        print (f"{member} is not a member")

# Retreieves and list all members ( This method might need revisiting if the membership expands)
def get_members():
    data = get_file()
    print(data)

# Get the correct stage, only handles dev and prod
def get_stage(bucket):
    session = boto3.session.Session()
    s3_resource = session.resource('s3')
    if(s3_resource.meta.client.head_bucket(Bucket=f"dev-{bucket}")):
        return "dev-"
    elif(s3_resource.meta.client.head_bucket(Bucket=f"prod-{bucket}")):
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

#Create a parser that takes CLI cmds and requires the use of the subparser
parser = argparse.ArgumentParser()
subp = parser.add_subparsers(dest='cmd')
subp.required = True

# Create subparsers
add_member_parser = subp.add_parser('add', help='Add a member to quicksight')
remove_member_parser = subp.add_parser('remove', help='Remove a member from quicksight')
get_members_parser = subp.add_parser('get', help='Lists quicksight members')

#Add arguments for the subparsers
add_member_parser.add_argument("--name", help="Members username", required=True)
add_member_parser.add_argument("--email", help="Members email address", required=True)
add_member_parser.add_argument("--group", help="The groups the person is a member of", required=True)

remove_member_parser.add_argument("--member", help="Username of the member", required=True)

# Set functions for the subparsers
get_members_parser.set_defaults(func=get_members)
add_member_parser.set_defaults(func=add_member)
remove_member_parser.set_defaults(func=remove_member)

if __name__ == "__main__":
    args = parser.parse_args()
    try: # Without this the get command fails as it has 0 args
        args.func(args)
    except:
        args.func()
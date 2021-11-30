import boto3
import os
from botocore.exceptions import ClientError
import logging

s3_client = boto3.client('s3')
sts_client = boto3.client('sts')
account_response = str(sts_client.get_caller_identity()['Account'])
bucket = f"datalake-bucket-{account_response}"
location = "data/level-3/dora/"
path = "../misc-files/"

def get_stage(bucket):
    session = boto3.session.Session()
    s3_resource = session.resource('s3')
    if(s3_resource.meta.client.head_bucket(Bucket=f"dev-{bucket}")):
        return "dev-"
    elif(s3_resource.meta.client.head_bucket(Bucket=f"prod-{bucket}")):
        return "prod-"
    else:
        return False

def upload_file(file_name, bucket):
    stage = get_stage(bucket)
    print(stage)
    try:
        response = s3_client.upload_file(path + file_name, f"{stage}{bucket}", location + file_name)
    except ClientError as e:
        logging.error(e)
    return response

def main():
    upload_file("manifest.json",bucket)
    upload_file("dora_users.csv",bucket)

if __name__ == "__main__":
    main()
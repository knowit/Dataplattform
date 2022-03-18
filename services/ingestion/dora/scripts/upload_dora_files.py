import boto3
import os
from botocore.exceptions import ClientError
import logging
import json

s3 = boto3.resource('s3')
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
    try:
        response = s3_client.upload_file(path + file_name, f"{stage}{bucket}", location + file_name)
    except ClientError as e:
        logging.error(e)
    return response

def upload_frequency(file_name, bucket):
    stage = get_stage(bucket)
    try:
        response = s3_client.upload_file(path + file_name, f"{stage}{bucket}", location+'frequency/' + file_name)
    except ClientError as e:
        logging.error(e)
    return response

def get_bucket(bucket):
    return s3.Bucket(bucket)

def isfile_s3(bucket, key: str) -> bool:
    """Returns T/F whether the file exists."""
    bucky = get_bucket(bucket)
    objs = list(bucky.objects.filter(Prefix=location + key))
    return len(objs) == 1 and objs[0].key == location + key

def create_manifest():

    manifest_data = {
        "fileLocations": [
            {
                "URIs": [
                    "s3://dev-datalake-bucket-"+account_response+"/data/level-3/dora/quicksight_role_bindings.csv"
                ]
            }
        ],
        "globalUploadSettings": {
            "format": "CSV",
            "delimiter": ",",
            "textqualifier": "'",
            "containsHeader": "true"
        }
    }

    json_string = json.dumps(manifest_data, indent=2)
    jsonFile = open("../misc-files/manifest.json", "w")
    jsonFile.write(json_string)
    jsonFile.close()

if __name__ == "__main__":
    stage = get_stage(bucket)
    create_manifest()
    print(isfile_s3(f"{stage}{bucket}", "dora_users.csv"))
    if not isfile_s3(f"{stage}{bucket}", "dora_usersa.csv"):
        upload_file("dora_users.csv",f"{stage}{bucket}")
    upload_file("manifest.json",f"{stage}{bucket}")
    upload_frequency('frequency.csv',f"{stage}{bucket}")
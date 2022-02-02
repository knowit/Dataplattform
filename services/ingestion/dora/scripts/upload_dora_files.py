import boto3
import os
from botocore.exceptions import ClientError
import logging
import json

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
    print(json_string)
    jsonFile = open("../misc-files/manifest.json", "w")
    jsonFile.write(json_string)
    jsonFile.close()

def main():
    create_manifest()
    upload_file("manifest.json",bucket)
    upload_file("dora_users.csv",bucket)
    upload_frequency('frequency.csv',bucket)

if __name__ == "__main__":
    main()
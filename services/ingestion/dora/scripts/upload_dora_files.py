import boto3
from botocore.exceptions import ClientError
import logging
import json

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
sts_client = boto3.client('sts')
root_dir = "data/level-3/dora/"
path = "../misc-files/"


def get_bucket_name():
    if s3_client.head_bucket(Bucket=f"dev-{base_name}"):
        return f'dev-{base_name}'
    elif s3_client.head_bucket(Bucket=f"prod-{base_name}"):
        return f'prod-{base_name}'

    return False


def upload_file(file_name, location=root_dir):
    try:
        response = s3_client.upload_file(path + file_name, bucket, location + file_name)
        return response
    except ClientError as e:
        logging.error(e)


def get_bucket():
    return s3.Bucket(bucket)


def isfile_s3(key: str) -> bool:
    """Returns T/F whether the file exists."""
    bucky = get_bucket()
    objs = list(bucky.objects.filter(Prefix=root_dir + key))
    return len(objs) == 1 and objs[0].key == root_dir + key


def create_manifest():
    manifest_data = {
        "fileLocations": [
            {
                "URIs": [
                    "s3://dev-datalake-bucket-" + account_id + "/data/level-3/dora/quicksight_role_bindings.csv"
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
    json_file = open('../misc-files/manifest.json', 'w')
    json_file.write(json_string)
    json_file.close()


if __name__ == "__main__":
    account_id = str(sts_client.get_caller_identity()['Account'])
    base_name = f'datalake-bucket-{account_id}'
    bucket = get_bucket_name()

    create_manifest()
    if not isfile_s3('dora_users.csv'):
        upload_file('dora_users.csv')
    upload_file('manifest.json')
    upload_file('frequency.csv', location=f'{root_dir}frequency/')

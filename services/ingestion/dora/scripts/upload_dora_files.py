import boto3
from botocore.exceptions import ClientError
import json

session = boto3.Session()
s3 = session.resource('s3')
s3_client = session.client('s3')
sts_client = session.client('sts')
account_response = str(sts_client.get_caller_identity()['Account'])
datalake_bucket = f"datalake-bucket-{account_response}"
stage = "dev"
location = "data/level-3/dora/"
path = "../misc-files/"


def get_stage(bucket):
    s3_resource = session.resource('s3')
    try:
        s3_resource.meta.client.head_bucket(Bucket=f"dev-{bucket}")
        return "dev"
    except ClientError:
        try:
            s3_resource.meta.client.head_bucket(Bucket=f"prod-{bucket}")
            return "prod"
        except ClientError as e:
            raise Exception(e)


def upload_file(file_name, bucket):
    try:
        response = s3_client.upload_file(path + file_name, f"{bucket}", location + file_name)
        return response
    except ClientError as e:
        raise Exception(e)


def upload_frequency(file_name, bucket):
    try:
        response = s3_client.upload_file(path + file_name, f"{bucket}", location + 'frequency/' + file_name)
        return response
    except ClientError as e:
        raise Exception(e)


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
                    "s3://" + stage + "-datalake-bucket-" + account_response + "/data/level-3/dora"
                                                                               "/quicksight_role_bindings.csv "
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
    json_file = open("../misc-files/manifest.json", "w+")
    json_file.write(json_string)
    json_file.close()


if __name__ == "__main__":
    stage = get_stage(datalake_bucket)
    create_manifest()
    if not isfile_s3(f"{stage}-{datalake_bucket}", "dora_users.csv"):
        upload_file("dora_users.csv", f"{stage}-{datalake_bucket}")
        print("Success")
    else:
        print(f"dora_users.csv already exists in bucket {stage}-{datalake_bucket}")
    upload_file("manifest.json", f"{stage}-{datalake_bucket}")
    upload_frequency('frequency.csv', f"{stage}-{datalake_bucket}")

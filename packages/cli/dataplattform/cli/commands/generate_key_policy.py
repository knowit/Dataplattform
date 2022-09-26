from argparse import ArgumentParser, Namespace
import boto3
import json


def get_account_id():
    client = boto3.client("sts")
    return client.get_caller_identity()["Account"]


def init(parser: ArgumentParser):
    parser.add_argument('-r', '--roles', default=[], type=str, nargs='*')


def run(args: Namespace, _):
    statement = [
        {
            "Sid": "Enable IAM User Permissions",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::" + str(get_account_id()) + ":root"
            },
            "Action": "kms:*",
            "Resource": "*"
        },
        {
            "Sid": "Enable encryption for loggroup",
            "Effect": "Allow",
            "Principal": {
                "Service": "logs.eu-central-1.amazonaws.com"
            },
            "Action": [
                "kms:Encrypt*",
                "kms:Decrypt*",
                "kms:ReEncrypt*",
                "kms:GenerateDataKey*",
                "kms:Describe*"
            ],
            "Resource": "*",
            "Condition": {
                "ArnLike": {
                    "kms:EncryptionContext:aws:logs:arn": "arn:aws:logs:eu-central-1:" +
                                                          str(get_account_id()) +
                                                          ":log-group:/aws-glue/crawlers-role/Level4GlueRole-"
                                                          "KMSGlueEncryptionConfigurations"
                }
            }
        }
    ]

    for role in args.roles:
        statement.append({
            "Sid": "Enable encryption for " + str(role),
            "Effect": "Allow",
            "Principal": {
                "Service": "logs.eu-central-1.amazonaws.com"
            },
            "Action": [
                "kms:Encrypt*",
                "kms:Decrypt*",
                "kms:DescribeKey*",
                "kms:GenerateDataKey*",
                "kms:ListKeys*"
            ],
            "Resource": "*",
            "Condition": {
                "StringLike": {
                    "aws:PrincipalArn": "arn:aws:iam::" + str(get_account_id()) + ":role/" + str(role)
                }
            }
        })

    policy = {
        "Version": "2012-10-17",
        "Id": "kms-key-policy-" + str(get_account_id()),
        "Statement": statement,
    }

    with open("my_key_policy.json", "w") as outfile:
        json.dump(policy, outfile, indent=4)

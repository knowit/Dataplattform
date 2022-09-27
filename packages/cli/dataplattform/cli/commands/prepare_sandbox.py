from argparse import ArgumentParser, Namespace
import boto3
import datetime
from typing import List


class IllegalAWSAccountException(Exception):
    pass


CERTIFICATE_REGION = 'us-east-1'


def create_parameter(name: str, value: str) -> None:
    client = boto3.client('ssm')
    client.put_parameter(
        Name=name,
        Value=value,
        Type='String',
        Overwrite=True
    )


def create_certificate(domain_name: str) -> dict:
    client = boto3.client('acm', region_name=CERTIFICATE_REGION)
    response = client.request_certificate(
        DomainName=domain_name,
        ValidationMethod='DNS',
        SubjectAlternativeNames=[f"*.{domain_name}"]
    )
    return response


def create_hosted_zone(domain_name: str) -> dict:
    client = boto3.client('route53')
    response = client.create_hosted_zone(
        Name=domain_name,
        CallerReference=str(datetime.datetime.now()),
        HostedZoneConfig={
            'Comment': 'For validering av SSL-sertifikatet før tjenestene deployes til sandbox.'
        },
    )
    return response


def create_record_for_validation(hosted_zone_id: str, cert_arn: str) -> None:
    acm = boto3.client('acm', region_name=CERTIFICATE_REGION)
    response = acm.describe_certificate(
        CertificateArn=cert_arn
    )
    route53 = boto3.client('route53')
    validation_record = [dvo['ResourceRecord'] for dvo in response['Certificate']['DomainValidationOptions']][0]
    route53.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'CREATE',
                    'ResourceRecordSet': {
                        'Name': validation_record['Name'],
                        'Type': validation_record['Type'],
                        'ResourceRecords': [
                            {
                                'Value': validation_record['Value']
                            }
                        ],
                        'TTL': 300
                    }
                }
            ]
        }
    )


def write_name_servers_to_file(path: str, name_servers: List[str]) -> None:
    with open(path, 'w') as f:
        for ns in name_servers:
            f.write(ns + '\n')


def init(parser: ArgumentParser):
    parser.add_argument("--domain-name", required=True)
    parser.add_argument("--stage", default='dev', choices=['dev', 'prod'])


def run(args: Namespace, _):
    bucket_names = [b["Name"] for b in boto3.client("s3").list_buckets()["Buckets"]]
    if "dev-dataplattform-deploymentbucket" in bucket_names or "prod-dataplattform-deploymentbucket" in bucket_names:
        raise IllegalAWSAccountException(
            "You are trying to use the sandbox script outside of your sandbox, i.e. in either the dev or prod "
            "environment.")
    cert_response = create_certificate(args.domain_name)
    hosted_zone_response = create_hosted_zone(args.domain_name)
    create_record_for_validation(hosted_zone_response['HostedZone']['Id'], cert_response['CertificateArn'])
    create_parameter(f"/{args.stage}/USEA1/sslIdentifier", cert_response['CertificateArn'].split(':')[-1])
    create_parameter(f"/{args.stage}/routes/domain_name", args.domain_name)
    write_name_servers_to_file('my_name_servers.txt', hosted_zone_response['DelegationSet']['NameServers'])

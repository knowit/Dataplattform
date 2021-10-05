from argparse import ArgumentParser, Namespace
import boto3

def init(parser: ArgumentParser):
    parser.add_argument("--domain-name", required=True)
    parser.add_argument("--stage", default='dev', choices=['dev', 'prod'])

def create_domain_parameter(domain_name: str, stage: str):
    client = boto3.client('ssm')


def create_certificate(domain_name: str):
    client = boto3.client('acm')
    response = client.request_certificate(
        DomainName=domain_name,
        ValidationMethod='DNS',
        SubjectAlternativeNames=[f"*.{domain_name}"]
    )
    return response['CertificateArn']

def create_certificate_parameter(cert_id: str, stage: str):
    pass 

def create_hosted_zone(domain_name: str):
    pass 

def create_records_for_validation(domain_name: str):
    pass

def run(args: Namespace, _):
    print(args)
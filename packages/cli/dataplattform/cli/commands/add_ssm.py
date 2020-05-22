from argparse import ArgumentParser, Namespace
import boto3


def interactive(value=None, type_=None):
    type_ = type_ or int(
        input("Type of parameter(1, 2, or 3)? 1=String, 2=StringList, 3=SecureString:"))
    types = ["String", "StringList", "SecureString"]
    type_ = types[type_ - 1]
    value = value or input("Value:")
    name = input("Name:")
    description = input("Description:")
    stage = input("Stage(dev, test, prod):")
    service = input("Service:")
    overwrite = bool(input("Overwrite existing value, true/false?:"))

    tags = [{
        'Key': 'Project',
        'Value': 'Dataplattform'
    }]

    while True:
        if input("Add new tag? y/n:") == "y":
            tag_key = input("Key:")
            tag_value = input("Value:")
            tags.append({"Key": tag_key, "Value": tag_value})
        else:
            break

    return add_parameter(stage, service, name, value, type_, description, overwrite, tags)


def add_parameter(stage, service, name, value, type_, description, overwrite, tags):
    client = boto3.client('ssm')

    finalName = "/" + stage + "/" + service + "/" + name

    client.put_parameter(
        Name=finalName,
        Description=description,
        Value=value,
        Type=type_,
        Overwrite=overwrite,
        Tier='Standard'
    )
    client.add_tags_to_resource(
        ResourceType='Parameter',
        ResourceId=finalName,
        Tags=tags
    )

    return finalName


def init(parser: ArgumentParser):
    parser.add_argument('-i --interactive', default=False, dest='interactive', action='store_true')

    parser.add_argument('-e', '--stage', default='dev', choices=['dev', 'test', 'prod'])
    parser.add_argument('-n', '--name')
    parser.add_argument('-v', '--value')
    parser.add_argument('-s', '--service')
    parser.add_argument('-t', '--type', dest='type_', choices=["String", "StringList", "SecureString"])
    parser.add_argument('-d', '--desc', default='')
    parser.add_argument('--overwrite', default=False, action='store_true')


def run(args: Namespace, parser: ArgumentParser):
    if args.interactive:
        response = interactive()
    else:
        for req in ['name', 'value', 'service', 'type_']:
            if getattr(args, req) is None:
                parser.error(f'--{req} is required')

        response = add_parameter(
            args.stage,
            args.service,
            args.name,
            args.value,
            args.type_,
            args.desc,
            args.overwrite, [{
                'Key': 'Project',
                'Value': 'Dataplattform'
            }])

    print(f"Final name: {response}")

import boto3
from dataplattform.cli.commands.add_ssm import interactive
from argparse import ArgumentParser, Namespace


def generatePassword(length):
    client = boto3.client('secretsmanager')

    response = client.get_random_password(
        PasswordLength=length,
        ExcludeNumbers=False,
        ExcludePunctuation=True,
        ExcludeUppercase=False,
        ExcludeLowercase=False,
        IncludeSpace=False,
        RequireEachIncludedType=False
    )

    finalName = interactive(response["RandomPassword"], 3)

    return finalName


def init(parser: ArgumentParser):
    pass


def run(args: Namespace, _):
    name = generatePassword(64)
    print("Final name: " + name)

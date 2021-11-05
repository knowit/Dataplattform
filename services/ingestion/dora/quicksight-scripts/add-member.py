import boto3
import argparse
import sys

quicksight_client = boto3.client('quicksight')
sts_client = boto3.client('sts')
account_response = str(sts_client.get_caller_identity()['Account'])


def add_member(name, group):
    quicksight_client.create_group_membership(
        MemberName=name,
        GroupName=group,
        AwsAccountId=account_response,
        Namespace='default'
    )


def add_user(name, email):
    quicksight_client.register_user(
        IdentityType='QUICKSIGHT',
        Email=email,
        UserRole='READER',
        AwsAccountId=account_response,
        Namespace='default',
        UserName=name,
        # ExternalLoginDeferationProviderType = 'COGNITO' - For the future
    )


def add_several_users(names, email, group):
    for i in len(names):
        add_user(names[i], email[i])
        add_member(names[i], group)


def add_single_user(name, email, group):
    add_user(name, email)
    add_member(name, group)


def main():
    if isinstance(sys.argv[1], list):
        if type(sys.argv[1]) is not list:
            raise (Exception("The emails needs to be in a list"))
        add_several_users(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        add_single_user(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()

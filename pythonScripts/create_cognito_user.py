import boto3
import json
from argparse import ArgumentParser

levels = [None, 'level2', 'level3']


def main():
    parser = ArgumentParser('')
    parser.add_argument('--username', dest='username', required=True, help='Users email')
    parser.add_argument('--password', dest='password', required=False, help='Password')
    parser.add_argument('--access-level', dest='access', required=False, choices=[1, 2, 3],
                        default=1, type=int, help='Users access level')
    parser.add_argument('--profile', dest='profile', required=False,
                        default='default', help='aws profile name')
    parser.add_argument('--delete', dest='delete', required=False,
                        action='store_true', help='Delete user with username')
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile)
    client = session.client('cognito-idp')

    user_pools = client.list_user_pools(MaxResults=1)
    user_pool = user_pools['UserPools'][0]['Id']
    if args.delete:
        client.admin_delete_user(UserPoolId=user_pool, Username=args.username)
        print("User deleted")
        return

    user_attributes = [{
        'Name': 'email',
        'Value': args.username
    }]
    user = client.admin_create_user(UserPoolId=user_pool, Username=args.username, MessageAction='SUPPRESS',
                                    TemporaryPassword=args.password, UserAttributes=user_attributes)
    username = user['User']['Username']
    client.admin_set_user_password(UserPoolId=user_pool, Username=username, Password=args.password,
                                   Permanent=True)
    if args.access != 1:
        client.admin_add_user_to_group(UserPoolId=user_pool, Username=username, GroupName=levels[args.access - 1])

    user_client = client.list_user_pool_clients(UserPoolId=user_pool)['UserPoolClients'][0]['ClientId']

    response = client.initiate_auth(
        ClientId=user_client,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': args.username,
            'PASSWORD': args.password
        })
    print(json.dumps(response, indent=4))


if __name__ == "__main__":
    main()

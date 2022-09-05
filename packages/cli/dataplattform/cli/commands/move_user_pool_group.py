from argparse import ArgumentParser, Namespace
import boto3


class UserPoolNotFoundException(Exception):
    pass


class LevelMoveException(Exception):
    pass


class EmptyGroupException(Exception):
    pass


def get_user_pool_id(user_pool_name: str) -> str:
    client = boto3.client('cognito-idp')
    response = client.list_user_pools(
        MaxResults=10
    )
    for pool in response['UserPools']:
        if pool['Name'] == user_pool_name:
            return pool['Id']
    raise UserPoolNotFoundException(f'User pool \'{user_pool_name}\' not found.')


def get_users_from_group(user_pool_id: str, group_name: str) -> dict:
    client = boto3.client('cognito-idp')
    response = client.list_users_in_group(
        UserPoolId=user_pool_id,
        GroupName=group_name
    )
    return response


def move_users_to_group(user_pool_id: str, from_group: str, to_group: str, users_to_add: dict):
    if not users_to_add:
        raise EmptyGroupException(f'Found no users to move from group \'{from_group}\'')
    client = boto3.client('cognito-idp')
    moved = []
    for user in users_to_add:
        username = user['Username']
        client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=to_group
        )
        client.admin_remove_user_from_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=from_group
        )
        for attribute in user['Attributes']:
            if attribute['Name'] == 'email':
                username = attribute['Value']
                break
        moved.append(username)
    print(f'Moved users {moved} from \'{from_group}\' to \'{to_group}\'')


def init(parser: ArgumentParser):
    parser.add_argument('-u', '--userpool', required=True)
    parser.add_argument('-f', '--from-group', required=True, default='level1',
                        choices=['level1', 'level2', 'level3', 'level4'])
    parser.add_argument('-t', '--to-group', required=True, default='level2',
                        choices=['level1', 'level2', 'level3', 'level4'])


def run(args: Namespace, _):
    if args.from_group == args.to_group:
        raise LevelMoveException('to-group and from-group parameters cannot be equal')
    user_pool_id = get_user_pool_id(args.userpool)
    users = get_users_from_group(user_pool_id, args.from_group)['Users']
    move_users_to_group(user_pool_id, args.from_group, args.to_group, users)
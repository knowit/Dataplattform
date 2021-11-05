import boto3


def main():
    cognito_client = boto3.client('cognito-idp')
    quicksight_client = boto3.client('quicksight')

    user_pools = cognito_client.list_user_pools(MaxResults=50)
    dora_user_pool = [pool for pool in user_pools['UserPools'] if pool['Name'] == 'dev-dora-user-pool'][0]
    dora_user_pool_id = dora_user_pool['Id']

    dora_users = cognito_client.list_users(UserPoolId=dora_user_pool_id).get('Users')

    print(dora_users)

    quicksight_users = quicksight_client.list_users(
        AwsAccountId='826278518019',
        Namespace='default'
    ).get('UserList')

    print(quicksight_users)

    for user in dora_users:
        email = [attribute['Value'] for attribute in user['Attributes'] if attribute['Name'] == 'email'][0]
        response = quicksight_client.register_user(
            IdentityType='QUICKSIGHT',
            Email=email,
            UserName=email,
            UserRole='READER',
            AwsAccountId='826278518019',
            Namespace='default',
        )
        print(response)


if __name__ == '__main__':
    main()

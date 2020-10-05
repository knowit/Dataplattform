import boto3
client = boto3.client('ssm')
region = 'eu-central-1'
userpool_id = client.get_parameter(Name='/dev/cloudfront-raw-storage/user_pool_id',
                                   WithDecryption=False).get('Parameter', {}).get('Value', '')

keys_url = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(region, userpool_id)
f = open('env_variables.py', 'w')
f.write('keys_url=' + repr(keys_url))
f.close()

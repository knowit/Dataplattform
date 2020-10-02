import json
import time
import boto3
import urllib.request
from jose import jwk, jwt
from jose.utils import base64url_decode


region = 'eu-central-1'
client = boto3.client('ssm')
userpool_id = client.get_parameter(Name='/dev/cloudfront-raw-storage/user_pool_id', 
                                   WithDecryption=False).get('Parameter', {}).get('Value', '')
keys_url = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(region, userpool_id)


with urllib.request.urlopen(keys_url) as f:
    response = f.read()
keys = json.loads(response.decode('utf-8'))['keys']


def handler(event, context):
    print(event)

    request = event['Records'][0]['cf']['request']
    headers = request['headers']
    token = headers['authorization'].split(" ")[1]
    if not token:
        return {"status": 401,
                "statusDescription": 'Token is not valid'}

    headers = jwt.get_unverified_headers(token)
    kid = headers['kid']

    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    if key_index == -1:
        #  'Public key not found in jwks.json'
        return {"status": 401,
                "statusDescription": 'Token is not valid'}

    public_key = jwk.construct(keys[key_index])

    message, encoded_signature = str(token).rsplit('.', 1)
    decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        return {"status": 401,
                "statusDescription": 'Token is not valid'}
    claims = jwt.get_unverified_claims(token)

    if time.time() > claims['exp']:
        return {"status": 401,
                "statusDescription": 'Token has expired'}

    return request

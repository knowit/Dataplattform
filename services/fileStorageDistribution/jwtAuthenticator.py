import json
import time
import urllib.request
from jose import jwk, jwt
from jose.utils import base64url_decode
from env_variables import keys_url


with urllib.request.urlopen(keys_url) as f:
    response = f.read()
keys = json.loads(response.decode('utf-8'))['keys']


def handler(event, context):
    request = event['Records'][0]['cf']['request']
    headers = request['headers']

    try:
        token = headers.get('authorization', '')[0]['value'].split(" ")[1]
    except Exception as e:
        print('Token missing, message:', e)
        return {"status": 401}

    headers = jwt.get_unverified_headers(token)
    kid = headers['kid']

    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    if key_index == -1:
        print('Public key not found in jwks.json')
        return {"status": 401}

    public_key = jwk.construct(keys[key_index])

    message, encoded_signature = str(token).rsplit('.', 1)
    decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        print('Token is not valid')
        return {"status": 401}
    claims = jwt.get_unverified_claims(token)

    if time.time() > claims['exp']:
        print('Token has expired')
        return {"status": 401}

    request['headers'].pop('authorization')
    return request

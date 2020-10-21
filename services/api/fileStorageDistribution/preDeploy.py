import argparse

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--userpool_id", required=True, help="Id of Cognito user pool")
    ap.add_argument("--region", required=True, help="Region of the Cognito user pool stack")
    kwargs = vars(ap.parse_args())
    keys_url = f'https://cognito-idp.{kwargs["region"]}.amazonaws.com/{kwargs["userpool_id"]}/.well-known/jwks.json'
    f = open('env_variables.py', 'w')
    f.write('keys_url=' + repr(keys_url))
    f.close()

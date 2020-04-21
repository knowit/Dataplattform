import boto3
from flask import Flask, request
from flask_restx import Api

from controller import temp_controller  # noqa: F401
from apis import open_api, authenticated_api


authorizations = {
    'access_toke': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'authorizer'
    }
}

app = Flask(__name__)
api = Api(app, title="Dataplattform", description="Dataplattform API", authorizations=authorizations)

api.add_namespace(open_api, path='/api/v1/test-open')
api.add_namespace(authenticated_api, path='/api/v1/authenticated/test-closed')


@app.before_request
def set_iam_role():
    event = request.environ.get('serverless.event')
    if event:
        role = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('cognito:roles', None)
        if role:
            client = boto3.client('sts')
            client.assume_role(
                RoleArn=role,
                RoleSessionName='APIrole'
            )


if __name__ == "__main__":
    app.run()

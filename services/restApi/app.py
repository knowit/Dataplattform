import boto3
from flask import Flask, jsonify, Blueprint, request
from flask_restplus import Api, Resource, Namespace

from controller import test_controller
from apis import TEST_OPEN_API, TEST_LOGIN_API


blueprint = Blueprint('api', __name__)

api = Api(blueprint, title="Dataplattform", description="Dataplattform API")

api.add_namespace(TEST_OPEN_API, path='/api/v1/test-open')
api.add_namespace(TEST_LOGIN_API, path='/api/v1/login/test-closed')

app = Flask(__name__)
app.register_blueprint(blueprint)


@app.before_request
def set_iam_role():
    event = request.environ['serverless.event']
    role = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('cognito:roles', None)
    print(role)
    if role:
        client = boto3.client('sts')
        client.assume_role(
            RoleArn=role,
            RoleSessionName='APIrole'
        )


if __name__ == "__main__":
    app.run()

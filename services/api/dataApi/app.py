
from flask import Flask
from flask_restx import Api
from os import environ
from flask_cors import CORS
from dataplattform.api import flask_ext

from apis.query import ns as query_ns
from apis.report import ns as report_ns
from apis.catalogue import ns as catalogue_ns


auth_url = 'dev-auth.dataplattform.knowit.no' \
    if environ.get('STAGE', 'dev') == 'dev' else 'auth.dataplattform.knowit.no'

app = Flask(__name__)

api = Api(
    app,
    title='Dataplattform API',
    doc=False,  # Use dedicated swagger UI
    security=[{'oauth2': ['openid']}],
    authorizations={
        'oauth2': {
            'type': 'oauth2',
            'flow': 'implicit',
            'authorizationUrl': f'https://{auth_url}/oauth2/authorize',
            'scopes': {
                'openid': ''
            }
        }
    })
user_session = flask_ext.UserSession(app)
CORS(app)

api.add_namespace(query_ns)
api.add_namespace(report_ns)
api.add_namespace(catalogue_ns)


@app.route('/schema.json')
def doc():
    swagger_schema = api.__schema__
    swagger_schema['basePath'] = '/'
    return swagger_schema


if __name__ == "__main__":
    app.run(debug=True)

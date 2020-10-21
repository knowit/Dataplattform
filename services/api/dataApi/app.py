
from flask import Flask
from flask_restx import Api
from dataplattform.api import flask_ext

from apis.query import ns as query_ns
from apis.report import ns as report_ns


app = Flask(__name__)
api = Api(app, title='Dataplattform API')
user_session = flask_ext.UserSession(app)

api.add_namespace(query_ns)
api.add_namespace(report_ns)


if __name__ == "__main__":
    app.run()

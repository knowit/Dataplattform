from flask import Flask
from flask_restx import Api, Namespace
from dataplattform.api import flask_ext

app = Flask(__name__)
api = Api(app, title='Dataplattform Data catalogue API')
ns = Namespace('catalogue')

user_session = flask_ext.UserSession(app)
api.add_namespace(ns)

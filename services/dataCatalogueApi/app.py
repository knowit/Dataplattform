from flask import Flask
from flask_restx import Api, Resource
from dataplattform.api import flask_ext
import core.routines as routines
import core.models as models
import boto3

app = Flask(__name__)
api = Api(app, title='Dataplattform Data catalogue API')
user_session = flask_ext.UserSession(app)

table_model = models.create_table_model(api)
database_model = models.create_database_model(api)


@api.route('/')
class RootRoute(Resource):
    def get(self):
        return {}


@api.route('/database/', strict_slashes=False)
class Databases(Resource):
    @api.marshal_with(database_model)
    @api.doc(model=database_model)
    def get(self):
        glue_client = boto3.client('glue')
        return routines.get_all_databases(api, glue_client)


@api.route('/table/', strict_slashes=False)
class Tables(Resource):
    def get(self):
        glue_client = boto3.client('glue')
        return routines.get_all_tables(api, glue_client)


@api.route('/table/<string:table_name>', strict_slashes=False)
class SingleTable(Resource):
    @api.marshal_with(table_model)
    @api.doc(model=table_model)
    def get(self, table_name):
        glue_client = boto3.client('glue')
        return routines.get_single_table(api, glue_client, table_name)


@api.route('/database/<string:database_name>/', strict_slashes=False)
@api.response(404, 'Database not found')
@api.doc(params={'database_name': 'Name of database'})
class Database(Resource):
    @api.marshal_with(database_model)
    @api.doc(model=database_model)
    def get(self, database_name):
        glue_client = boto3.client('glue')
        return routines.get_database_content(api, glue_client, database_name)


@api.route('/database/<string:database_name>/table/<string:table_name>')
@api.response(404, 'Table not found')
@api.response(404, 'Database not found')
@api.doc(params={'table_name': 'Name of a table in the database',
                 'database_name': 'Name of database'})
class Table(Resource):
    @api.marshal_with(table_model)
    @api.doc(model=table_model)
    def get(self, database_name, table_name):
        glue_client = boto3.client('glue')
        return routines.get_table(api, glue_client, database_name, table_name)


if __name__ == '__main__':
    app.run(debug=True)

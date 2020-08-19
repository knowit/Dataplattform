from flask import Flask
from flask_restx import Api, Resource, fields
from dataplattform.api import flask_ext
import boto3
import botocore.exceptions

app = Flask(__name__)
user_session = flask_ext.UserSession(app)

api = Api(app, title='Dataplattform Data catalogue')
ns = api.namespace('', description='Dataplattform databases')


def get_tables(glue_client, database_name):
    try:
        db_tables = glue_client.get_tables(DatabaseName=database_name)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'EntityNotFoundException':
            api.abort(404, 'Database ' + database_name + ' not found')
        else:
            raise error
    return db_tables


@ns.route('/')
class Root(Resource):
    def get(self):
        return 200


database_resource_fields = {'name': fields.String}
database_resource_fields['tables'] = fields.List(fields.String)
database_resource_fields['createTime'] = fields.DateTime
database = api.model('Database', database_resource_fields)

table_resource_fields = {'name': fields.String}
table_resource_fields['databaseName'] = fields.String
table_resource_fields['createTime'] = fields.DateTime
table_resource_fields['updateTime'] = fields.DateTime
table_resource_fields['lastAccessTime'] = fields.DateTime

col_field = {}
col_field['Name'] = fields.String
col_field['Type'] = fields.String
#table_resource_fields['columns'] = fields.List(fields.Nested(col_field))
table_resource_fields['columns'] = fields.Raw
table_resource_fields['partitionKeys'] = fields.Raw
table = api.model('Table', table_resource_fields)


@ns.route('/database/<string:database_name>/')
@ns.response(404, 'Database not found')
@ns.doc(params={'database_name': 'Name of database'})
class DatabaseNames(Resource):
    @ns.marshal_with(database)
    @ns.doc(model=database)
    def get(self, database_name):
        glue_client = boto3.client('glue')
        db = glue_client.get_database(Name=database_name)
        print(db)
        db_tables = get_tables(glue_client, database_name)
        db_table_names = [table['Name'] for table in db_tables['TableList']]
        data = {}
        data['name'] = db['Database']['Name']
        data['createTime'] = db['Database']['CreateTime']
        data['tables'] = db_table_names
        return data


@ns.route('/database/<string:database_name>/table/<string:table_name>')
@ns.response(404, 'Table not found')
@ns.doc(params={'table_name': 'Name of a table in the database',
                'database_name': 'Name of database'})
class TableContent(Resource):
    @ns.marshal_with(table)
    def get(self, database_name, table_name):
        glue_client = boto3.client('glue')
        db_tables = get_tables(glue_client, database_name)
        table_list = db_tables['TableList']

        def create_dict(table_name, table_list):
            def find_elem(table_name, table_list):
                for table in table_list:
                    if table['Name'] == table_name:
                        return table
                return {}

            tmpDict = find_elem(table_name, table_list)
            if not tmpDict:
                api.abort(404, 'Table not ' + table_name + ' found')

            data = {'name': table_name,
                    'databaseName': tmpDict['DatabaseName'],
                    'createTime': tmpDict['CreateTime'].isoformat(),
                    'updateTime': tmpDict['UpdateTime'].isoformat(),
                    'lastAccessTime': tmpDict['LastAccessTime'].isoformat(),
                    'columns': tmpDict['StorageDescriptor']['Columns'],
                    'partitionKeys': tmpDict['PartitionKeys']
                    }
            return data

        db_data = create_dict(table_name, table_list)
        return db_data


if __name__ == '__main__':
    app.run(debug=True)

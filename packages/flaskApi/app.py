from flask import Flask
from flask_restful import Resource, Api
import boto3

app = Flask(__name__)

api = Api(app)

glue_client = boto3.client('glue')
databases = glue_client.get_databases()
db_list = databases['DatabaseList']
db_names = [db['Name'] for db in db_list]


class DatabaseNames(Resource):
    def get(self):
        return {'database_names': db_names}


class DatabaseTables(Resource):
    def get(self, database_name):
        db_tables = glue_client.get_tables(DatabaseName=database_name)
        db_table_names = [table['Name'] for table in db_tables['TableList']]
        return {'avaliable_tables': db_table_names}


class TableContent(Resource):
    def get(self, database_name, table_name):
        db_tables = glue_client.get_tables(DatabaseName=database_name)
        table_list = db_tables['TableList']

        def create_dict(table_name, table_list):

            def find_elem(table_name, table_list):
                for table in table_list:
                    if table['Name'] == table_name:
                        return table
                return {}

            tmpDict = find_elem(table_name, table_list)

            return {'DatabaseName': tmpDict['DatabaseName'],
                    'CreateTime': tmpDict['CreateTime'].isoformat(),
                    'UpdateTime': tmpDict['UpdateTime'].isoformat(),
                    'LastAccessTime': tmpDict['LastAccessTime'].isoformat(),
                    'Columns': tmpDict['StorageDescriptor']['Columns'],
                    'PartitionKeys': tmpDict['PartitionKeys']
                    }

        db_data = create_dict(table_name, table_list)

        return {table_name: db_data}


api.add_resource(DatabaseNames, '/database_names')
api.add_resource(DatabaseTables, '/database_names/<database_name>')
api.add_resource(TableContent, '/database_names/<database_name>/<table_name>')


if __name__ == '__main__':
    app.run(debug=True)

from flask_restx import Resource, fields, Namespace
from common.repositories.catalogue import (
    TableRepository, DatabaseRepository,
    GlueRepositoryException, GlueRepositoryNotFoundException
)

ns = Namespace('Catalogue', path="/catalogue")

DatabaseModel = ns.model(
    'Database', {
        'name': fields.String,
        'tables': fields.List(fields.String),
        'createTime': fields.DateTime
    })

ColumnModel = ns.model(
    'Column', {
        'name': fields.String,
        'type': fields.String
    })

TableModel = ns.model(
    'Table', {
        'name': fields.String,
        'databaseName': fields.String,
        'createTime': fields.DateTime,
        'updateTime': fields.DateTime,
        'lastAccessTime': fields.DateTime,
        'columns': fields.List(fields.Nested(ColumnModel)),
    })


@ns.route('/database', strict_slashes=False)
class DatabaseList(Resource):
    @ns.marshal_with(DatabaseModel, as_list=True)
    @ns.doc(model=DatabaseModel)
    def get(self):
        try:
            database_repository = DatabaseRepository()
            table_repository = TableRepository()
            return [
                {
                    'name': db['Name'],
                    'tables': [table['Name'] for table in table_repository.all(db['Name'])],
                    'createTime': db['CreateTime']
                }
                for db in database_repository.all()
            ]
        except (GlueRepositoryException, Exception) as e:
            ns.abort(500, str(e))


@ns.route('/table', strict_slashes=False)
class TableList(Resource):
    @ns.marshal_with(TableModel, as_list=True)
    @ns.doc(model=TableModel)
    def get(self):
        try:
            database_repository = DatabaseRepository()
            table_repository = TableRepository()
            return [
                {
                    'name': table['Name'],
                    'databaseName': table['DatabaseName'],
                    'createTime': table['CreateTime'],
                    'updateTime': table['UpdateTime'],
                    'lastAccessTime': table['LastAccessTime'],
                    'columns': [
                        {'name': column['Name'], 'type': column['Type']}
                        for column in [*table['StorageDescriptor']['Columns'], *table['PartitionKeys']]
                    ]
                }
                for db in database_repository.all() for table in table_repository.all(db['Name'])
            ]
        except (GlueRepositoryException, Exception) as e:
            ns.abort(500, str(e))


@ns.route('/database/<string:database_name>')
@ns.doc(params={'database_name': 'Name of database'})
class Database(Resource):
    @ns.marshal_with(DatabaseModel)
    @ns.doc(model=DatabaseModel)
    def get(self, database_name):
        try:
            database_repository = DatabaseRepository()
            table_repository = TableRepository()

            db = database_repository.get(database_name)
            return {
                'name': db['Name'],
                'tables': [table['Name'] for table in table_repository.all(db['Name'])],
                'createTime': db['CreateTime']
            }
        except GlueRepositoryNotFoundException:
            ns.abort(404)
        except (GlueRepositoryException, Exception) as e:
            ns.abort(500, str(e))


@ns.route(
    '/table/<string:table_name>',
    doc={
        'params': {
            'table_name': 'Name of a table in the database'
        }
    })
@ns.route(
    '/database/<string:database_name>/table/<string:table_name>',
    doc={
        'params': {
            'table_name': 'Name of a table in the database',
            'database_name': 'Name of database'
        }
    })
class Table(Resource):
    @ns.marshal_with(TableModel)
    @ns.doc(model=TableModel)
    def get(self, **kwargs):
        try:
            table_repository = TableRepository()
            table = table_repository.get(kwargs['database_name'], kwargs['table_name']) \
                if 'database_name' in kwargs else None

            if table is None:
                for database in DatabaseRepository().all():
                    try:
                        table = table_repository.get(database['Name'], kwargs['table_name'])
                    except GlueRepositoryNotFoundException:
                        continue

            if table is None:
                raise GlueRepositoryNotFoundException()

            return {
                'name': table['Name'],
                'databaseName': table['DatabaseName'],
                'createTime': table['CreateTime'],
                'updateTime': table['UpdateTime'],
                'lastAccessTime': table['LastAccessTime'],
                'columns': [
                    {'name': column['Name'], 'type': column['Type']}
                    for column in [*table['StorageDescriptor']['Columns'], *table['PartitionKeys']]
                ]
            }

        except GlueRepositoryNotFoundException:
            ns.abort(404)
        except (GlueRepositoryException, Exception) as e:
            ns.abort(500, str(e))


if __name__ == '__main__':
    app.run(debug=True)

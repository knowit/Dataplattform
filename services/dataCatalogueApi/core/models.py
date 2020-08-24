from flask_restx import fields


def create_database_model(api):
    return api.model('Database', {
                    'name': fields.String,
                    'tables': fields.List(fields.String),
                    'createTime': fields.DateTime
                    })


def create_table_model(api):

    colum_model = api.model('Column', {
                            'name': fields.String,
                            'type': fields.String
                            })

    return api.model('Table', {
                            'name': fields.String,
                            'databaseName': fields.String,
                            'createTime': fields.DateTime,
                            'updateTime': fields.DateTime,
                            'lastAccessTime': fields.DateTime,
                            'columns':   fields.List(fields.Nested(colum_model)),
                            'partitionKeys': fields.List(fields.Nested(colum_model))})

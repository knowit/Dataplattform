from flask_restx import fields
from api import api

DatabaseModel = api.model(
    'Database', {
        'name': fields.String,
        'tables': fields.List(fields.String),
        'createTime': fields.DateTime
    })

ColumnModel = api.model(
    'Column', {
        'name': fields.String,
        'type': fields.String
    })

TableModel = api.model(
    'Table', {
        'name': fields.String,
        'databaseName': fields.String,
        'createTime': fields.DateTime,
        'updateTime': fields.DateTime,
        'lastAccessTime': fields.DateTime,
        'columns':   fields.List(fields.Nested(ColumnModel)),
    })

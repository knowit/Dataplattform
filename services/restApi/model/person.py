from flask_restx import fields
from apis import open_api, authenticated_api


class PersonResponse:
    open_model = open_api.model('Test', {
        'name': fields.String(required=True, description="Name of person"),
        'age': fields.Integer(required=True, description="Age of person")
    })

    login_model = authenticated_api.model('Test', {
        'name': fields.String(required=True, description="Name of person"),
        'age': fields.Integer(required=True, description="Age of person")
    })

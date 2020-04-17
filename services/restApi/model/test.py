from flask_restplus import fields
from apis import TEST_OPEN_API, TEST_LOGIN_API


class TestResponse:
    open_model = TEST_OPEN_API.model('Test', {
        'name': fields.String(required=True, description="Name of person"),
        'age': fields.Integer(required=True, description="Age of person")
    })

    login_model = TEST_LOGIN_API.model('Test', {
        'name': fields.String(required=True, description="Name of person"),
        'age': fields.Integer(required=True, description="Age of person")
    })

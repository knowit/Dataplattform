from flask_restplus import fields
from apis import TEST_API


class TestResponse:
    model = TEST_API.model('Test', {
        'name': fields.String(required=True, description="Name of person"),
        'age': fields.Integer(required=True, description="Age of person")
    })

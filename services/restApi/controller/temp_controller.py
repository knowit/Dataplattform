from flask_restx import Resource, marshal_with  # noqa: F401

from apis import open_api, authenticated_api
from model.person import PersonResponse
from repository.temp_repository import Temp_repository


test_repository = Temp_repository()


@open_api.route('/', strict_slashes=False)
class Tests(Resource):
    @open_api.marshal_with(PersonResponse.open_model)
    def get(self):
        return test_repository.get_all()


@open_api.route('/<string:name>')
class TestByName(Resource):
    @open_api.marshal_with(PersonResponse.open_model)
    def get(self, name):
        return test_repository.get_person_by_name(name)


@authenticated_api.route('/', strict_slashes=False)
@authenticated_api.doc(security='access_toke')
class TestsSecure(Resource):
    @authenticated_api.marshal_with(PersonResponse.login_model)
    @authenticated_api.doc(security='access_toke')
    def get(self):
        return test_repository.get_all()


@authenticated_api.route('/<string:name>')
@authenticated_api.doc(security='access_toke')
class TestByNameSecure(Resource):
    @authenticated_api.marshal_with(PersonResponse.login_model)
    def get(self, name):
        return test_repository.get_person_by_name(name)

from flask import Flask, request, after_this_request
from flask_restplus import Resource, marshal_with

from apis import TEST_OPEN_API, TEST_LOGIN_API
from model.test import TestResponse
from repository.test_repository import Test_repository


#test_repository = Test_repository()
test_data = [
	    {"name": "Testersen", "age": 73},
	    {"name": "Bjarne", "age": 7},
	    {"name": "Potet", "age": 22}
	]


@TEST_OPEN_API.route('/', strict_slashes=False)
class Tests(Resource):
    @TEST_OPEN_API.marshal_with(TestResponse.open_model)
    def get(self):
        return test_data


@TEST_OPEN_API.route('/<string:name>')
class TestByName(Resource):
    @TEST_OPEN_API.marshal_with(TestResponse.open_model)
    def get(self, name):
    	return [x for x in test_data if x['name'] == name]


@TEST_LOGIN_API.route('/', strict_slashes=False)
class Tests(Resource):
    @TEST_LOGIN_API.marshal_with(TestResponse.login_model)
    def get(self):
        return test_data


@TEST_LOGIN_API.route('/<string:name>')
class TestByName(Resource):
    @TEST_LOGIN_API.marshal_with(TestResponse.login_model)
    def get(self, name):
        return [x for x in test_data if x['name'] == name]
from flask import Flask, request, after_this_request
from flask_restplus import Resource, marshal_with

from apis import TEST_API
from model.test import TestResponse
from repository.test_repository import Test_repository


#test_repository = Test_repository()
test_data = [
	    {"name": "Testersen", "age": 73},
	    {"name": "Bjarne", "age": 7},
	    {"name": "Potet", "age": 22}
	]


@TEST_API.route('/', strict_slashes=False)
class Tests(Resource):
    @TEST_API.marshal_with(TestResponse.model)
    def get(self):
        return test_data


@TEST_API.route('/<string:name>')
class TestByName(Resource):
    @TEST_API.marshal_with(TestResponse.model)
    def get(self, name):
    	return test_data

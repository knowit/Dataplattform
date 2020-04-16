
from flask import Flask, jsonify, Blueprint
from flask_restplus import Api, Resource, Namespace

from controller import test_controller
from apis import TEST_API

blueprint = Blueprint('api', __name__)

api = Api(blueprint, title="Dataplattform", description="Dataplattform API")

api.add_namespace(TEST_API, path='/test')

app = Flask(__name__)
app.register_blueprint(blueprint)

if __name__ == "__main__":
    app.run()

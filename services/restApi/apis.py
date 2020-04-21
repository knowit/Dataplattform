from flask_restx import Namespace

open_api = Namespace('Test open API', description='My open test api')
authenticated_api = Namespace('Test authenticated API', description='My authentication test api')

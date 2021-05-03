import common.services.athena_engine as engine
from flask_restx import Resource, Namespace, fields
from flask import Response
from common.repositories.reports import ReportsRepository
import common.services.cache_table_service as cache_table_service


ns = Namespace('Employee', path='/data')

parser = ns.parser()
parser.add_argument(
    'email',
    type=str,
    dest='email',
    required=True)
parser.add_argument(
    'format',
    type=str,
    dest='output_format',
    default='json',
    choices=['json', 'csv'])

QueryRequest = ns.model(
    'Query', {
        'email': fields.String(),
        'format': fields.String(default='json', enum=['json', 'csv']),
    })


#Nye endepunktet
@ns.route('/email', strict_slashes=False)
@ns.doc(
    responses={400: 'Validation Error'},
    produces=['application/json', 'text/csv']
)
class Email(Resource):
    def email(self,email, output_format):
        sql = "select * from active_directory where email is " + email
        df = engine.execute(sql)

        if output_format == 'csv':
            return Response(
                df.to_csv(index=False),
                content_type='text/csv')
        else:
            return Response(
                df.to_json(orient='records'),
                content_type='application/json')


@ns.route('/query', strict_slashes=False)
@ns.doc(
    responses={400: 'Validation Error'},
    produces=['application/json', 'text/csv']
)
class Query(Resource):
    def query(self, sql, output_format):
        df = engine.execute(sql)

        if output_format == 'csv':
            return Response(
                df.to_csv(index=False),
                content_type='text/csv')
        else:
            return Response(
                df.to_json(orient='records'),
                content_type='application/json')

    @ns.expect(parser)
    @ns.doc(security={'oauth2': ['openid']})
    def get(self):
        args = parser.parse_args()
        try:
            return self.query(args.sql, args.output_format)
        except Exception as e:
            ns.abort(500, e)

    @ns.expect(QueryRequest)
    @ns.doc(security={'oauth2': ['openid']})
    def post(self):
        try:
            return self.query(ns.payload['sql'], ns.payload.get('format', 'json'))
        except Exception as e:
            ns.abort(500, e)


class FilterType:
    __schema__ = {'type': 'string', 'format': 'field:value'}

    def __call__(self, value: str):
        field, _, value = value.partition(':')
        return field, value


filter_parser = ns.parser()
filter_parser.add_argument(
    'filter',
    type=FilterType(),
    dest='filter',
    action='append')


@ns.route('/query/report/<name>', strict_slashes=False)
class QueryReport(Resource):
    @ns.expect(filter_parser)
    @ns.doc(security={'oauth2': ['openid']})
    def get(self, name):
        filters = filter_parser.parse_args().get('filter', [])

        with ReportsRepository() as repo:
            report = repo.get(name)

        query = cache_table_service.query_cache_table(
            report['dataProtection'], report['name'])

        return Response(
            query(filters),
            content_type='application/json')

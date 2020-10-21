import common.services.athena_engine as engine
from flask_restx import Resource, Namespace, fields
from flask import Response
from common.repositories.reports import ReportsRepository
import common.services.cache_table_service as cache_table_service


ns = Namespace('Query', path='/data')

parser = ns.parser()
parser.add_argument(
    'sql',
    type=str,
    dest='sql',
    required=True)
parser.add_argument(
    'format',
    type=str,
    dest='output_format',
    default='json',
    choices=['json', 'csv'])

QueryRequest = ns.model(
    'Query', {
        'sql': fields.String(),
        'format': fields.String(default='json', enum=['json', 'csv']),
    })


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
    def get(self):
        args = parser.parse_args()
        try:
            return self.query(args.sql, args.output_format)
        except Exception as e:
            ns.abort(500, e)

    @ns.expect(QueryRequest)
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
    def get(self, name):
        filters = filter_parser.parse_args().get('filter', [])

        with ReportsRepository() as repo:
            report = repo.get(name)

        query = cache_table_service.query_cache_table(
            report['dataProtection'], report['name'])

        return Response(
            query(filters),
            content_type='application/json')

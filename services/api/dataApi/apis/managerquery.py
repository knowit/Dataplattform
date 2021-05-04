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
    def email(self, email_address, output_format):
        sql = "select * from active_directory where email is " + email_address
        df = engine.execute(sql)

        if output_format == 'csv':
            return Response(
                df.to_csv(index=False),
                content_type='text/csv')
        else:
            return Response(
                df.to_json(orient='records'),
                content_type='application/json')
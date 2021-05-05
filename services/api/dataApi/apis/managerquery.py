import common.services.athena_engine as engine
from flask_restx import Resource, Namespace, fields
from flask import Response
from common.repositories.reports import ReportsRepository
import common.services.cache_table_service as cache_table_service


ns = Namespace('ManagerQuery', path='/employee')

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

EmployeeModel = ns.model(
    'Employee', {
        'email': fields.String(),
        'format': fields.String(default='json', enum=['json', 'csv']),
    })


@ns.route('/email', strict_slashes=False)
@ns.doc(
    responses={400: 'Validation Error'},
    produces=['application/json', 'text/csv']
)
class Email(Resource):
    def email(self, email_address, output_format):
        sql = "select * from active_directory where email is " + email_address
        #df = engine.execute(sql)
        return "yes"

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
    @ns.doc(model=EmployeeModel)
    def get(self):
        args = parser.parse_args()
        try:
            return self.email(args.email, args.output_format)
        except Exception as e:
            ns.abort(500, e)
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

EmployeeModel = ns.model(
    'Employee', {
        'guid' : fields.String(),
        'displayname': fields.String(),
        'email': fields.String(),
        'manager': fields.Nested(EmployeeModel)
    })


@ns.route('/email', strict_slashes=False)
@ns.doc(
    responses={400: 'Validation Error'},
    produces=['application/json', 'text/csv']
)
class Email(Resource):
    def email(self, email_address):
        email = "" if email_address is None else 'where a.email=\''+email_address+'\''
        emp_sql = 'select a.guid,a.displayname,a.email,b.guid,b.displayname,b.email,c.guid,c.displayname,c.email from active_directory a left outer join active_directory b on a.managerguid = b.guid left outer join active_directory c on b.managerguid = c.guid ' + email
        df = engine.execute(emp_sql)
        data_json = df.to_json(orient='records')

        def setUser(data, keys , n):
            if(len(keys) > (n) and (data[keys[n]] is not None)):
                person = {}
                person[keys[0]] = data[keys[n]]
                person[keys[1]] = data[keys[n+1]]
                person[keys[2]] = data[keys[n+2]]
                manager = setUser(data,keys,n+3)
                person['manager'] = manager
                return person
            else:
                return None
            
        list_of_users = []
        for user in data_json:
            keys = list(user.keys())
            user_details = setUser(user,keys,0)
            list_of_users.append(user_details)

        return Response(
            list_of_users,
            content_type='application/json')

    @ns.expect(parser)
    @ns.doc(security={'oauth2': ['openid']})
    @ns.doc(model=EmployeeModel)
    def get(self):
        args = parser.parse_args()
        try:
            return self.email(args.email)
        except Exception as e:
            ns.abort(500, e)
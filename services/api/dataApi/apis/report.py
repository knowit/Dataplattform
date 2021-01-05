# from api import api
from flask_restx import Resource, Namespace, fields
from common.repositories.reports import ReportsRepository
import common.services.report_service as report_service

ns = Namespace('Report', path='/data')

ReportModel = ns.model(
    'Report', {
        'name': fields.String(),
        'queryString': fields.String(),
        'tables': fields.List(fields.String()),
        'dataProtection': fields.Integer(),
        'created': fields.DateTime(),
        'lastUsed': fields.DateTime(required=False),
        'lastCacheUpdate': fields.DateTime(required=False)
    })


CreateReportModel = ns.model(
    'CreateReport', {
        'name': fields.String(),
        'queryString': fields.String(),
    })


@ns.route('/report', strict_slashes=False)
class Report(Resource):
    @ns.marshal_with(ReportModel, as_list=True)
    @ns.doc(security={'oauth2': ['openid']})
    def get(self):
        with ReportsRepository() as repo:
            return repo.all()

    @ns.expect(CreateReportModel)
    @ns.marshal_with(ReportModel, code=201)
    @ns.doc(security={'oauth2': ['openid']})
    def post(self):
        return report_service.new_report(ns.payload)


@ns.route('/report/<name>', strict_slashes=False)
@ns.param('name', 'Name of the report')
class ReportItem(Resource):
    @ns.response(204, 'Report deleted')
    @ns.doc(security={'oauth2': ['openid']})
    def delete(self, name):
        try:
            return report_service.delete_report(name), 204
        except KeyError:
            return f'Could not find ${name}', 404

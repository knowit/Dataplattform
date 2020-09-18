from flask import Flask, request, Response
from flask_swagger import swagger
from dataplattform.api import flask_ext
import engine
import json

app = Flask(__name__)
session = flask_ext.UserSession(app)


@app.route('/data/')
@app.route('/data/spec')
def spec():
    doc = swagger(app)
    doc['info']['version'] = "1.0"
    doc['info']['title'] = "Dataplattform Data API"
    return doc


@app.route('/data/query', methods=['GET', 'POST'])
def query():
    """
    Query dataplattform data
    ---
    produces:
    - application/json
    - text/csv
    responses:
        '200':
            description: Query result as json records or csv
        '500':
            description: Error
    parameters:
    -   name: sql
        in: query
        description: SQL query string
        required: true
        type: string
    -   name: format
        in: query
        description: csv or json output format, default json
        required: false
        type: string
    """

    def options(args):
        return args.get('sql'), args.get('format', 'json')

    query_str, output_format = options(request.args if request.method == 'GET' else request.get_json(force=True))

    if query_str is None:
        return Response(
            json.dumps({'error': 'parameter \'sql\' is required'}),
            status=500,
            content_type='application/json')

    try:
        return Response(
            engine.execute(query_str, output_format),
            content_type='text/csv' if output_format == 'csv' else 'application/json')
    except Exception as e:
        print(e)
        return Response(
            json.dumps({'error': f'error executing query with sql: \'{query_str}\''}),
            status=500,
            content_type='application/json')


if __name__ == "__main__":
    app.run()

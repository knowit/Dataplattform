from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import requests
import xmltodict
import numpy as np


handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:

    def fetch_yr_data(location) -> list:
        url = f'https://www.yr.no/place/{location}/varsel_time_for_time.xml'
        data = xmltodict.parse(requests.get(url).text)

        location_name = data.get('weatherdata', {}).get('location', {}).get('name', {})
        forecasts = data.get('weatherdata', {}).get('forecast', {}).get('tabular', {}).get('time', {})

        def timestring_to_posix(time):
            return int(datetime.strptime(time, '%Y-%m-%dT%H:%M:%S').timestamp())

        def data_point(forecast):
            return {
                'location': location,
                'location_name': location_name,
                'time_from': timestring_to_posix(forecast['@from']),
                'time_to': timestring_to_posix(forecast['@to']),
                'precipitation': float(forecast['precipitation']['@value']),
                'wind_speed': float(forecast['windSpeed']['@mps']),
                'temperature': int(forecast['temperature']['@value']),
                'air_pressure': float(forecast['pressure']['@value']),
            }

        return [data_point(forecasts[i]) for i in range(0, min(len(forecasts), 24))]

    locations = [
        'Norway/Oslo/Oslo/Lakkegata'
        # TODO: more locations
        ]

    return Data(
        metadata=Metadata(
            timestamp=datetime.now().timestamp()
        ),
        data=np.hstack([fetch_yr_data(location) for location in locations]).tolist())

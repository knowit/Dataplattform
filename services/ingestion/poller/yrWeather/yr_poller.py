from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import requests
import xmltodict
import numpy as np
import pandas as pd
from typing import Dict


handler = Handler()


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

@handler.process(partitions={'yr_weather':['location_name', 'time', 'time_from', 'time_to']})
def process(data) -> Dict[str, pd.DataFrame]:

    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        df = pd.json_normalize(payload)
        df['time'] = int(metadata['timestamp'])
        return df

    df = pd.concat([make_dataframe(d) for d in data])

    # TODO: Check for duplicates?
    return {
        'yr_weather': df
    }

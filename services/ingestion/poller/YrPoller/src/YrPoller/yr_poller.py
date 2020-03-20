from datetime import datetime
import boto3
import os
import json
import time
import requests
import logging

import xmltodict


def handler(event, context):
    poll()

    return {
        'statusCode': 200,
        'body': 'Success',
    }


def poll():
    # If you want more locations, add that to this dict. Key will be folder in s3 it will be uploaded to
    locations = {"Lakkegata": "Norway/Oslo/Oslo/Lakkegata"}

    data_points = {}

    for key, location in locations.items():
        data_points[key] = get_yr_data(location)

    path = os.getenv("ACCESS_PATH")

    for folder, data in data_points.items():
        logging.info(f"sending data to s3 about {folder}")
        s3 = boto3.resource('s3')
        s3_object = s3.Object(
            os.getenv('DATALAKE'), f"{path}{folder}/" + str(int(time.time())) + ".json")
        s3_object.put(Body=(bytes(json.dumps(data).encode('UTF-8'))))

    return True


def get_yr_data(location) -> list:
    logging.info(f"Getting weather-information for {location}")
    url = f"https://www.yr.no/place/{location}/varsel_time_for_time.xml"
    # Maybe add some catch here if unsuccessful
    data = xmltodict.parse(requests.get(url).content)

    def timestring_to_posix(time):
        # utc_offset = int(data["weatherdata"]["location"]["timezone"]["@utcoffsetMinutes"])
        # uts_delta = timedelta(minutes=utc_offset)
        new_time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")  # + utx_delta
        return int(new_time.timestamp())

    location_name = data.get("weatherdata", {}).get("location", {}).get(
        "name", {})  # Will return {} if non-existing
    forecasts = data.get("weatherdata", {}).get("forecast", {}).get(
        "tabular", {}).get("time", {})  # {} if non-existing
    ret = []
    for i in range(0, min(len(forecasts), 24)):  # At most insert 25 hours of weather data
        forecast = forecasts[i]
        time_from = timestring_to_posix(forecast.get("@from", None))
        data_point = {
            "location": location,
            "location_name": location_name,
            "time_from": time_from,
            "time_to": timestring_to_posix(forecast.get("@to", None)),
            "precipitation": float(forecast.get("precipitation", {}).get("@value", None)),
            "wind_speed": float(forecast.get("windSpeed", {}).get("@mps", None)),
            "temperature": int(forecast.get("temperature", {}).get("@value", None)),
            "air_pressure": float(forecast.get("pressure", {}).get("@value", None)),
        }
        ret.append(data_point)
    return ret


if __name__ == "__main__":
    poll()

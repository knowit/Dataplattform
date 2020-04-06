from dataplattform.common.handler import processor
import pandas as pd
from typing import Dict

handler = processor()


@handler.process(partitions=['location_name', 'time', 'time_from', 'time_to'])
def process(data) -> Dict[str, pd.DataFrame]:

    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data'].values()
        df = pd.json_normalize(payload)
        df['time'] = int(metadata['timestamp'])
        return df

    df = pd.concat([make_dataframe(d) for d in data])

    # TODO: Check for duplicates?
    return {
        'yr_weather': df
    }


if __name__ == "__main__":
    from dataplattform.testing.events import S3Records, S3Record, S3Put, S3Object
    from dataplattform.testing.helper import load_serverless_environment

    load_serverless_environment(verbose=True)

    handler(S3Records(
        records=[
            S3Record(
                s3=S3Put(
                    object_=S3Object(
                        key='data/level-1/yr/Lakkegata/1585011999.json'
                    )
                )
            )
        ]
    ).to_dict(), None)

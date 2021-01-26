from dataplattform.common.handlers.process import PersonDataProcessHandler
from dataplattform.common.repositories.person_repository import PersonIdentifierType
import pandas as pd
from typing import Dict


handler = PersonDataProcessHandler(PersonIdentifierType.ALIAS)


@handler.process(partitions={}, person_data_tables=['person_data_test_5'])
def process(data, events) -> Dict[str, pd.DataFrame]:
    out_df = pd.concat([pd.json_normalize(d.json()['data'])for d in data])
    return {'person_data_test_5': out_df}

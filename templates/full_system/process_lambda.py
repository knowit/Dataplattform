from dataplattform.common.handlers.process import PersonalProcessHandler
from dataplattform.common.repositories.person_repository import PersonIdentifierType
import pandas as pd
from typing import Dict


handler = PersonalProcessHandler(PersonIdentifierType.ALIAS)


@handler.process(partitions={})
def process(data, events) -> Dict[str, pd.DataFrame]:
    out_df = pd.concat([pd.json_normalize(d.json()['data'])for d in data])
    return {
        'olanor': {'some_structured_data': out_df}
        }

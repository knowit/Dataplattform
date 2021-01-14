from dataplattform.common.handlers.process import PersonalProcessHandler, ProcessHandler
from dataplattform.common.repositories.person_repository import PersonRepository, PersonIdentifierType
import pandas as pd
from typing import Dict


# handler = PersonalProcessHandler(PersonIdentifierType.ALIAS)
handler = ProcessHandler()


@handler.process(partitions={'person_data_test_4': ['guid']})
def process(data, events) -> Dict[str, pd.DataFrame]:

    def transform_to_guid(data):
        with PersonRepository() as repo:
            for item in data:
                item['guid'] = repo.get_guid_by(PersonIdentifierType.ALIAS, item['alias'])
                del item['alias']
        return data

    out_df = pd.concat([pd.json_normalize(transform_to_guid(d.json()['data']))for d in data])
    return {'person_data_test_4': out_df}

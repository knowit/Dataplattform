from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Union, Dict, List, AnyStr


@dataclass_json
@dataclass
class Metadata:
    timestamp: Union[int, float]


@dataclass_json
@dataclass
class Data:
    metadata: Metadata
    data: Union[AnyStr, Dict, List]

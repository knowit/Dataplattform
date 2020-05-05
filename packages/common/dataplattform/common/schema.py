from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Union, Dict, List, AnyStr
from datetime import datetime


@dataclass_json
@dataclass
class Metadata:
    timestamp: Union[int, float] = field(default_factory=lambda: datetime.now().timestamp())


@dataclass_json
@dataclass
class Data:
    data: Union[AnyStr, Dict, List]
    metadata: Metadata = field(default_factory=Metadata)

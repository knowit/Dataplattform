
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase
from typing import Dict, AnyStr


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class APIGateway:
    path_parameters: Dict[AnyStr, AnyStr] = field(default_factory=dict)
    headers: Dict[AnyStr, AnyStr] = field(default_factory=dict)
    body: AnyStr = ''

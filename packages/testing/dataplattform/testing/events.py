
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase, config
from typing import Dict, AnyStr, List


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class APIGateway:
    path_parameters: Dict[AnyStr, AnyStr] = field(default_factory=dict)
    headers: Dict[AnyStr, AnyStr] = field(default_factory=dict)
    body: AnyStr = ''


@dataclass_json
@dataclass
class S3Bucket:
    name: str = 'name'
    arn: str = ''


@dataclass_json
@dataclass
class S3Object:
    key: str = 'key'
    size: int = 1024


@dataclass_json
@dataclass
class S3Put:
    s3_schema_version: str = field(default='1.0', metadata=config(letter_case=LetterCase.CAMEL))
    configuration_id: str = field(default='', metadata=config(letter_case=LetterCase.CAMEL))
    bucket: S3Bucket = field(default_factory=S3Bucket)
    object_: S3Object = field(default_factory=S3Object, metadata=config(field_name='object'))


@dataclass_json
@dataclass
class S3Record:
    s3: S3Put = field(default_factory=S3Put)


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class S3Records:
    records: List[S3Record] = field(default_factory=list)

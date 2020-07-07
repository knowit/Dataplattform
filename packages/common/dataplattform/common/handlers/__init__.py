from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Response:
    status_code: int = 200
    body: str = ''


def make_wrapper_func(f, *return_type):
    def func(*args, **kwargs):
        result = f(*args, **kwargs)
        assert result is None or any([isinstance(result, t) for t in return_type]),\
            f'Return type {type(result).__name__} must be None or\
                any {", ".join([t.__name__ for t in return_type])}'
        return result
    return func


def verify_schema(dataset, dataframe, partitions):
    dataset_partitions = dataset.info.get('partitions', [])
    dataset_columns = dataset.columns + dataset_partitions

    if len(dataset_partitions) != len(partitions):
        return False

    if not all([a == b for a, b in zip(sorted(dataset_partitions), sorted(partitions))]):
        return False

    if len(dataset_columns) != len(dataframe.columns):
        return False

    if not all([a == b for a, b in zip(sorted(dataset_columns), sorted(dataframe.columns))]):
        return False

    if not all([dataset.dtypes[c] == dataframe.dtypes[c] for c in dataset.columns]):
        return False

    return True

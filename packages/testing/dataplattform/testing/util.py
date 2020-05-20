from contextlib import contextmanager
from moto import settings


@contextmanager
def ignore_policy():
    settings.INITIAL_NO_AUTH_ACTION_COUNT = float('inf')
    yield None
    settings.INITIAL_NO_AUTH_ACTION_COUNT = 0

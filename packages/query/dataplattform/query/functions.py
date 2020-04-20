from pypika import CustomFunction

# Presto datetime functions
from_iso8601_timestamp = CustomFunction('from_iso8601_timestamp', ['timestamp'])
from_iso8601_date = CustomFunction('from_iso8601_date', ['date'])
from_unixtime = CustomFunction('from_unixtime', ['time'])
to_iso8601 = CustomFunction('to_iso8601', ['date'])
to_unixtime = CustomFunction('to_unixtime', ['timestamp'])

# TODO: add presto functions
# https://prestodb.io/docs/0.172/functions.html

from warnings import warn
from dataplattform.common.handlers.mixed import MixedHandler
from dataplattform.common.handlers import Response as HandlerResponse

warn('handler import is moved to "dataplattform.common.handlers.mixed"', DeprecationWarning)
warn('Response import is moved to "dataplattform.common.handlers.Response"', DeprecationWarning)

Handler = MixedHandler
Response = HandlerResponse

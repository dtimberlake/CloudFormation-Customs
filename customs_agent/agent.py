import logging
import signal
from contextlib import contextmanager

from botocore.vendored import requests

from exceptions import InvalidRequestType, TimeoutError
from response import Response


@contextmanager
def _timeout(seconds):
    def _handle_timeout(_signum, _frame):
        raise TimeoutError

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, 0)


class Agent(object):
    def __init__(self):
        self.session = requests.session()
        self.logger = self._init_loggers()

    def __call__(self, event, context):
        response = self.calculate_response(event, context)
        response.send(self.session)

    def calculate_response(self, event, context):
        response = Response(event)
        self.logger = self._get_request_logger(event['RequestId'])
        try:
            with _timeout((
                              context.get_remaining_time_in_millis() - 500) / 1000.0):
                action = self._parse_action(event)
                action(event, context, response)

        except InvalidRequestType:
            response.reason = 'Invalid RequestType'

        except TimeoutError:
            response.reason = 'Function timed out'

        return response

    def create(self, event, context, logger):
        raise NotImplementedError

    def update(self, event, context, logger):
        raise NotImplementedError

    def delete(self, event, context, logger):
        raise NotImplementedError

    def _init_loggers(self, log_level='INFO'):
        logger = logging.getLogger('CFCustomsAgent')
        handler = logging.StreamHandler()

        log_format = '[%(requestid)s][%(asctime)s][%(levelname)s] %(message)s \n'
        handler.setFormatter(logging.Formatter(log_format))

        logger.addHandler(handler)
        logger.setLevel(getattr(logging, log_level.upper()))

        return self._get_request_logger('AgentInit')

    def _get_request_logger(self, request_id):
        return logging.LoggerAdapter(logging.getLogger('CFCustomsAgent'),
                                     {'requestid': request_id})

    def _parse_action(self, event):
        response_type = event.get('RequestType', '')
        action = getattr(self, response_type.lower(), None)
        if not action:
            raise InvalidRequestType
        return action

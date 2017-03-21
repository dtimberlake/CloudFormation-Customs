import logging
import signal
from abc import ABCMeta, abstractmethod
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
    __metaclass__ = ABCMeta

    def __new__(cls, *args, **kwargs):
        try:
            new_class = super(Agent, cls).__new__(cls, *args, **kwargs)
        except TypeError:
            new_class = InvalidAgent()
        return new_class

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
                action(event, response)

        except InvalidRequestType:
            response.reason = 'Invalid RequestType'

        except TimeoutError:
            response.reason = 'Function timed out'

        return response

    @abstractmethod
    def create(self, request, response):
        raise NotImplementedError

    @abstractmethod
    def update(self, request, response):
        raise NotImplementedError

    @abstractmethod
    def delete(self, request, response):
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


class InvalidAgent(Agent):
    def calculate_response(self, event, context):
        response = Response(event)
        response.reason = "Must provide implementations for all event "\
                          "handlers of Agent."
        return response

    def create(self, request, response):
        self._handle_request(response)

    def update(self, request, response):
        self._handle_request(response)

    def delete(self, request, response):
        self._handle_request(response)

    def _handle_request(self, response):
        response.status = "FAILED"
        response.data = "Must provide implementations for all event "\
                        "handlers of Agent."
import pytest


@pytest.fixture()
def event():
    return {
        'RequestType': 'RequestType',
        'ResponseURL': 'ResponseURL',
        'StackId': 'StackId',
        'RequestId': 'RequestId',
        'ResourceType': 'ResourceType',
        'LogicalResourceId': 'LogicalResourceId',
        'PhysicalResourceId': 'PhysicalResourceId',
        'ResourceProperties': {},
        'OldResourceProperties': {},
    }


@pytest.fixture()
def context():
    class Context(object):
        log_stream_name = "log_stream_name"

        def get_remaining_time_in_millis(self):
            return 2000

    return Context()

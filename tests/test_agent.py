import json
import logging
import time

from botocore.vendored import requests
import pytest

from customs_agent import Agent, Response
from customs_agent.exceptions import InvalidRequestType, TimeoutError
from fixtures import event, context

logging.getLogger().addHandler(logging.StreamHandler())


@pytest.fixture()
def agent():
    class MyAgent(Agent):
        def create(self, event, context, logger):
            return 'PhysicalResourceId', {'method': 'create'}

        def update(self, event, context, logger):
            return 'PhysicalResourceId', {'method': 'update'}

        def delete(self, event, context, logger):
            return 'PhysicalResourceId', {'method': 'delete'}

    agent = MyAgent()

    return agent


def assert_put_called_with(agent, event, status, data=None, reason=None,
                           physical_resource_id='PhysicalResourceId'):
    body = {
        'Status': status,
        'PhysicalResourceId': physical_resource_id,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
    }
    if data:
        body['Data'] = data
    if reason:
        body['Reason'] = reason
    agent._session.put.assert_called_once_with(
        event['ResponseURL'],
        data=json.dumps(body)
    )


def assert_logging_levels(log_level, boto_log_level):
    assert logging.getLogger().getEffectiveLevel() == log_level
    assert logging.getLogger('botocore').getEffectiveLevel() == boto_log_level
    assert logging.getLogger('boto3').getEffectiveLevel() == boto_log_level


class TestAgent(object):
    def test_agent_init_sets_up_logger(self):
        agent = Agent()
        assert agent.logger.logger.getEffectiveLevel() == logging.INFO

    def test_agent(self, event, context, mocker):
        agent = Agent()
        response = Response(event)

        mocker.patch.object(agent, 'calculate_response')
        mocker.patch.object(response, 'send')

        agent.calculate_response.return_value = response

        agent(event, context)

        response.send.assert_called_once()

    def test_unimplemented_methods(self, event, context):
        agent = Agent()

        with pytest.raises(NotImplementedError):
            event['RequestType'] = 'Create'
            agent.calculate_response(event, context)

        with pytest.raises(NotImplementedError):
            event['RequestType'] = 'Update'
            agent.calculate_response(event, context)

        with pytest.raises(NotImplementedError):
            event['RequestType'] = 'Delete'
            agent.calculate_response(event, context)

    def test_calculate_response(self, event, context):
        class MyAgent(Agent):
            def create(self, event, context, response):
                response.data = 'create data'
                response.status = 'SUCCESS'
        agent = MyAgent()

        event['RequestType'] = 'Create'

        response = agent.calculate_response(event, context)
        correct_response = Response(event)

        assert response.request_type == correct_response.request_type
        assert response.response_url == correct_response.response_url
        assert response.physical_resource_id == correct_response.physical_resource_id
        assert response.stack_id == correct_response.stack_id
        assert response.request_id == correct_response.request_id
        assert response.logical_resource_id == correct_response.logical_resource_id
        assert response.data == 'create data'
        assert not response.reason
        assert response.status == 'SUCCESS'

    def test_calculate_response_failed_action(self, event, context):
        class MyAgent(Agent):
            def create(self, event, context, response):
                response.reason = 'reason for failure'
        agent = MyAgent()

        event['RequestType'] = 'Create'

        response = agent.calculate_response(event, context)

        assert response.status == 'FAILED'
        assert response.reason == 'reason for failure'

    def test_calculate_response_bad_request_type(self, event, context):
        event['RequestType'] = 'BadRequestType'

        agent = Agent()

        response = agent.calculate_response(event, context)

        assert response.status == 'FAILED'
        assert response.reason == 'Invalid RequestType'

    def test_calculate_response_timeout(self, event, context, mocker):
        class MyAgent(Agent):
            def create(self, event, context, response):
                time.sleep(.002)

        agent = MyAgent()

        event['RequestType'] = 'Create'

        mocker.patch.object(context, 'get_remaining_time_in_millis')
        context.get_remaining_time_in_millis.return_value = 501

        response = agent.calculate_response(event, context)

        assert response.status == 'FAILED'
        assert response.reason == 'Function timed out'

    def test_calculate_response_updates_logger(self, event, context):
        class MyAgent(Agent):
            def create(self, event, context, response):
                pass

        agent = MyAgent()

        assert agent.logger.extra == {'requestid': 'AgentInit'}

        event['RequestType'] = 'Create'

        agent.calculate_response(event, context)

        assert agent.logger.extra == {'requestid': 'RequestId'}

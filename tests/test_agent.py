import json
import logging
import time

from customs_agent import Agent, Response
from customs_agent.agent import InvalidAgent
from fixtures import event, context

logging.getLogger().addHandler(logging.StreamHandler())


class BaseTestAgent(Agent):
    def create(self, request, response):
        return 'PhysicalResourceId', {'method': 'create'}

    def update(self, request, response):
        return 'PhysicalResourceId', {'method': 'update'}

    def delete(self, request, response):
        return 'PhysicalResourceId', {'method': 'delete'}


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
        agent = BaseTestAgent()
        assert agent.logger.logger.getEffectiveLevel() == logging.INFO

    def test_agent(self, event, context, mocker):
        agent = BaseTestAgent()
        response = Response(event)

        mocker.patch.object(agent, 'calculate_response')
        mocker.patch.object(response, 'send')

        agent.calculate_response.return_value = response

        agent(event, context)

        response.send.assert_called_once_with(agent.session)

    def test_unimplemented_methods(self, event, context):
        agent = Agent()
        event['RequestType'] = 'Create'

        response = agent.calculate_response(event, context)

        expected_reason = "Must provide implementations for all event " \
                          "handlers of Agent."
        expected_status = "FAILED"

        assert isinstance(agent, InvalidAgent)
        assert response.reason == expected_reason
        assert response.status == expected_status

    def test_calculate_response(self, event, context):
        class MyAgent(BaseTestAgent):
            def create(self, request, response):
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
        class MyAgent(BaseTestAgent):
            def create(self, request, response):
                response.reason = 'reason for failure'

        agent = MyAgent()

        event['RequestType'] = 'Create'

        response = agent.calculate_response(event, context)

        assert response.status == 'FAILED'
        assert response.reason == 'reason for failure'

    def test_calculate_response_bad_request_type(self, event, context):
        event['RequestType'] = 'BadRequestType'

        agent = BaseTestAgent()

        response = agent.calculate_response(event, context)

        assert response.status == 'FAILED'
        assert response.reason == 'Invalid RequestType'

    def test_calculate_response_timeout(self, event, context, mocker):
        class MyAgent(BaseTestAgent):
            def create(self, request, response):
                time.sleep(.002)

        agent = MyAgent()

        event['RequestType'] = 'Create'

        mocker.patch.object(context, 'get_remaining_time_in_millis')
        context.get_remaining_time_in_millis.return_value = 501

        response = agent.calculate_response(event, context)

        assert response.status == 'FAILED'
        assert response.reason == 'Function timed out'

    def test_calculate_response_updates_logger(self, event, context):
        class MyAgent(BaseTestAgent):
            def create(self, request, response):
                pass

        agent = MyAgent()

        assert agent.logger.extra == {'requestid': 'AgentInit'}

        event['RequestType'] = 'Create'

        agent.calculate_response(event, context)

        assert agent.logger.extra == {'requestid': 'RequestId'}

    def test_invalid_agent(self, event, context):
        class MyAgent(Agent):
            def create(self, request, resposne):
                pass

        agent = MyAgent()

        response = agent.calculate_response(event, context)

        assert response.status == 'FAILED'
        assert response.reason == "Must provide implementations for all event " \
                                  "handlers of Agent."

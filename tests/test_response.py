import json

from botocore.vendored import requests
import pytest

from customs_agent import Response
from fixtures import event


class TestResponse(object):
    def test_init(self, event):
        response = Response(event=event)

        assert response.response_url == event['ResponseURL']
        assert response.request_type == event['RequestType']
        assert response.physical_resource_id == event['PhysicalResourceId']
        assert response.stack_id == event['StackId']
        assert response.request_id == event['RequestId']
        assert response.logical_resource_id == event['LogicalResourceId']
        assert not response.data
        assert not response.reason
        assert response.status == 'FAILED'

    def test_certain_properties_should_be_immutable(self, event):
        response = Response(event=event)

        def assert_raises_attribute_error_on_set(attribute_name):
            with pytest.raises(AttributeError):
                setattr(response, attribute_name, "value")

        assert_raises_attribute_error_on_set('request_type')
        assert_raises_attribute_error_on_set('stack_id')
        assert_raises_attribute_error_on_set('request_id')
        assert_raises_attribute_error_on_set('logical_resource_id')
        assert_raises_attribute_error_on_set('response_url')

    def test_reason_must_be_success_or_failed(self, event):
        response = Response(event=event)

        with pytest.raises(AttributeError):
            response.status = 'NotFailedOrSuccess'

    def test_send(self, event, mocker):
        response = Response(event=event)

        response.data = {'key1': 'value1'}
        response.status = 'SUCCESS'

        mocker.patch.object(requests, 'put')

        response.send(requests)

        requests.put.assert_called_once_with(
            event['ResponseURL'],
            data=json.dumps({
                'Status': 'SUCCESS',
                'PhysicalResourceId': event['PhysicalResourceId'],
                'StackId': event['StackId'],
                'RequestId': event['RequestId'],
                'LogicalResourceId': event['LogicalResourceId'],
                'Data': {'key1': 'value1'}
            }))

    def test_send_with_response(self, event, mocker):
        response = Response(event=event)

        response.reason = "A reason"
        response.status = "FAILED"

        mocker.patch.object(requests, 'put')

        response.send(requests)

        requests.put.assert_called_once_with(
            event['ResponseURL'],
            data=json.dumps({
                'Status': 'FAILED',
                'PhysicalResourceId': event['PhysicalResourceId'],
                'StackId': event['StackId'],
                'RequestId': event['RequestId'],
                'LogicalResourceId': event['LogicalResourceId'],
                'Reason': 'A reason'
            }))

    def test_reason_must_be_set_if_failed(self, event, mocker):
        response = Response(event=event)

        response.status = "FAILED"

        mocker.patch.object(requests, 'put')

        response.send(requests)

        requests.put.assert_called_once_with(
            event['ResponseURL'],
            data=json.dumps({
                'Status': 'FAILED',
                'PhysicalResourceId': event['PhysicalResourceId'],
                'StackId': event['StackId'],
                'RequestId': event['RequestId'],
                'LogicalResourceId': event['LogicalResourceId'],
                'Reason': ''
            }))

    def test_success(self, event):
        expected_message = 'success message'
        response = Response(event)

        response.success(expected_message)

        assert response.reason == expected_message
        assert response.status == 'SUCCESS'

    def test_failed(self, event):
        expected_message = 'failed message'
        response = Response(event)

        response.failed(expected_message)

        assert response.reason == expected_message
        assert response.status == 'FAILED'
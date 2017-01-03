import json


class Response(object):
    def __init__(self, event):
        self.response_url = event['ResponseURL']
        self.request_type = event['RequestType']
        self.stack_id = event['StackId']
        self.request_id = event['RequestId']
        self.logical_resource_id = event['LogicalResourceId']
        self.data = ''
        self.reason = ''
        self.status = 'FAILED'

        # locks attributes since they must match what was sent in via the event
        self._locked_attributes = ['request_type', 'stack_id', 'request_id',
                                   'logical_resource_id', 'response_url']

        physical_resource_id = event.get('PhysicalResourceId')
        if physical_resource_id:
            self.physical_resource_id = event.get('PhysicalResourceId')
            self._locked_attributes.append('physical_resource_id')

    def __setattr__(self, name, value):
        if name in getattr(self, '_locked_attributes', []):
            raise AttributeError('Cannot change {}'.format(name))
        elif name == 'status' and value not in ['SUCCESS', 'FAILED']:
            raise AttributeError('status must be either "SUCCESS" or "FAILED"')
        super(Response, self).__setattr__(name, value)

    def send(self, session):
        body = {
            'Status': self.status,
            'PhysicalResourceId': self.physical_resource_id,
            'StackId': self.stack_id,
            'RequestId': self.request_id,
            'LogicalResourceId': self.logical_resource_id,
        }
        if self.data:
            body['Data'] = self.data
        if (self.reason or self.status == 'FAILED') \
                and isinstance(self.reason, str):
            body['Reason'] = self.reason

        session.put(self.response_url, data=json.dumps(body))

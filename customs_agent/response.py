import json


class Response(object):
    def __init__(self, event):
        self._response_url = event['ResponseURL']
        self._request_type = event['RequestType']
        self._stack_id = event['StackId']
        self._request_id = event['RequestId']
        self._logical_resource_id = event['LogicalResourceId']
        self._data = ''
        self._reason = ''
        self._status = 'FAILED'
        self._physical_resource_id = event.get('PhysicalResourceId')

    @property
    def response_url(self):
        return self._response_url

    @property
    def request_type(self):
        return self._request_type

    @property
    def stack_id(self):
        return self._stack_id

    @property
    def request_id(self):
        return self._request_id

    @property
    def logical_resource_id(self):
        return self._logical_resource_id

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def reason(self):
        return self._reason

    @reason.setter
    def reason(self, value):
        self._reason = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value in ['SUCCESS', 'FAILED']:
            self._status = value
        else:
            raise AttributeError('status must be either "SUCCESS" or "FAILED"')

    @property
    def physical_resource_id(self):
        return self._physical_resource_id

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

    def success(self, message):
        self.status = 'SUCCESS'
        self.reason = message

    def failed(self, message):
        self.status = 'FAILED'
        self.reason = message

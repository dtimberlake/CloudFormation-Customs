=============
Customs Agent
=============

.. image:: https://travis-ci.org/dtimberlake/customs_agent.svg?branch=master
    :target: https://travis-ci.org/dtimberlake/customs_agent

**Note**: This library is still in beta and the API may change.

Introduction
------------

Customs Agent is a helper library for building AWS CloudFormation custom
resources with AWS Lambda. Now you can focus on writing the provisioning
logic for your custom resource and let Customs Agent handle the
individual request routing and responses.

Features
--------

1. Automatic routing to create, update, or delete logic
2. Formatting of responses back to CloudFormation
3. Stops execution before timeout and sends failure response (no more
   dangling resources)
4. Simple and easy to use API

Install
-------

Temporary install while submit to PyPi:

``pip install customs_agent``

Getting Started
---------------

1. Create your agent class:

.. code-block:: python

    # handler.py
    from customs_agent import Agent

    class MyAgent(Agent):
        def create(self, event, context, response):
            self.logger.info("Creating resource")
            # create logic
            response.data = { 'name': 'my resource name' }
            response.physical_resource_id = 'my_resource_id'
            response.success('Success message')

    def update(self, event, context, response):
        #update logic

    def delete(self, event context, response):
        #delete logic


2. Create agent as handler:

.. code:: python

    agent = MyAgent()

3. Point AWS Lambda function to:

.. code:: python

    handler:agent

TODOs
-----

1. Documentation
2. Test utilities
from setuptools import setup, find_packages

import customs_agent

setup_options = dict(
    name='customs_agent',
    url='https://github.com/dtimberlake/customs_agent',
    version=customs_agent.__version__,
    description="Helper library for building AWS CloudFormation custom resources.",
    long_description=open("README.md").read(),
    author="Daniel Timberlake",
    packages=find_packages(exclude=['tests*']),
    license="Apache License 2.0",
)

setup(**setup_options)

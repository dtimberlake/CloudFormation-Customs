from setuptools import setup, find_packages

import customs_agent

setup_options = dict(
    name='customs_agent',
    url='https://github.com/dtimberlake/customs_agent',
    version=customs_agent.__version__,
    description="Helper library for building AWS CloudFormation custom resources.",
    long_description=open("README.rst").read(),
    author="Daniel Timberlake",
    author_email="daniel@danieltimberlake.com",
    download_url="https://github.com/dtimberlake/customs_agent/archive/0.1.0.tar.gz",
    packages=find_packages(exclude=['tests*']),
    license="MIT",
    keywords=["AWS", "CloudFormation", "Custom Resource"]
)

setup(**setup_options)

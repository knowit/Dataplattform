from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_common',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['dataclasses-json', 'boto3', 's3fs==0.4', 'fastparquet', 'pandas', 'aws-xray-sdk'],
    zip_safe=False)

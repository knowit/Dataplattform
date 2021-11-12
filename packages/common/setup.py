from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_common',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['dataclasses-json==0.5.6', 'boto3==1.18.55', 's3fs==0.4', 'fastparquet==0.7.1', 'pandas==1.1.5', 'aws-xray-sdk==2.8.0'],
    zip_safe=False)

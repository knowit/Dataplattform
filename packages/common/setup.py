from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_common',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['dataclasses-json==0.4', 'boto3==1.14', 's3fs==0.4', 'fastparquet==0.4', 'pandas==1.0'],
    zip_safe=False)

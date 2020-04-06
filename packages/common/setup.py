from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_common',
    packages=find_namespace_packages(include=['dataplattform.*'], exclude=["tests"]),
    install_requires=['dataclasses-json', 'boto3', 's3fs', 'fastparquet'],
    zip_safe=False)

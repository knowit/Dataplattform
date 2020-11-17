from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_testing',
    packages=find_namespace_packages(include=['dataplattform.*']),
    entry_points={"pytest11": ["dataplattform = dataplattform.testing.plugin"]},
    install_requires=['pytest==5.4', 'pytest-env==0.6.2', 'pytest-mock==3.1.0', 'moto==1.3.14',
                      'dataclasses-json==0.4', 'boto3', 'botocore', 'pyathena==1.11'],
    zip_safe=False)

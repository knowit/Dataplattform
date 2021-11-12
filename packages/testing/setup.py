from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_testing',
    packages=find_namespace_packages(include=['dataplattform.*']),
    entry_points={"pytest11": ["dataplattform = dataplattform.testing.plugin"]},
    install_requires=['pytest==6.2.5', 'pytest-env==0.6.2', 'pytest-mock==3.6.1', 'moto==1.3.14',
                      'dataclasses-json==0.5.6', 'boto3==1.18.55', 'botocore==1.21.55', 'pyathena==1.11'],
    zip_safe=False)

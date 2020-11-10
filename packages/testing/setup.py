from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_testing',
    packages=find_namespace_packages(include=['dataplattform.*']),
    entry_points={"pytest11": ["dataplattform = dataplattform.testing.plugin"]},
    install_requires=['pytest', 'pytest-env', 'pytest-mock', 'moto<1.3.15',
                      'dataclasses-json', 'boto3', 'botocore', 'pyathena<2.0.0'],
    zip_safe=False)

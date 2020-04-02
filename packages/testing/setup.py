from setuptools import setup, find_packages

setup(
    name='dataplattform_testing',
    packages=find_packages(),
    entry_points={"pytest11": ["dataplattform = dataplattform.testing.plugin"]},
    install_requires=['pytest', 'pytest-env', 'pytest-mock', 'moto', 'dataclasses-json'],
    zip_safe=False)

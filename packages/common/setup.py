from setuptools import setup, find_packages

setup(
    name='dataplattform_common',
    packages=find_packages(),
    install_requires=['dataclasses-json'],
    zip_safe=False)

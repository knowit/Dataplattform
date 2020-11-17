from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_api',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['boto3', 'flask==1.1', 'python-dateutil==2.8', 'cachetools'],
    dependency_links=['file:../common', 'file:../query'],
    zip_safe=False)

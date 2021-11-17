from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_query',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['pyathena==1.11', 'pandas==1.3.4', 'pypika==0.48.8'],
    zip_safe=False)

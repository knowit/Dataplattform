from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_query',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['pyathena==1.11', 'pandas==1.0', 'pypika==0.37'],
    zip_safe=False)

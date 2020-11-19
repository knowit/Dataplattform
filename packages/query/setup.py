from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_query',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['pyathena', 'pyathena[pandas]', 'pandas', 'pypika'],
    zip_safe=False)

from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_cli',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['boto3', 'requests', 'python-dateutil', 'pandas', 'fastparquet'],
    dependency_links=['file:../common'],
    entry_points={
        'console_scripts': [
            'dataplattform=dataplattform.cli:main',
        ],
    },
    zip_safe=False)

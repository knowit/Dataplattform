from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_cli',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['boto3', 'moto==1.3.14', 'requests==2.23',
                      'python-dateutil==2.8', 'pandas==1.0', 'fastparquet==0.4'],
    dependency_links=['file:../common', 'file:../query'],
    entry_points={
        'console_scripts': [
            'dataplattform=dataplattform.cli:main',
        ],
    },
    zip_safe=False)

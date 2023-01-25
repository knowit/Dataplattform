from setuptools import setup, find_namespace_packages

setup(
    name='dataplattform_cli',
    packages=find_namespace_packages(include=['dataplattform.*']),
    install_requires=['boto3==1.18.55', 'moto==1.3.14', 'requests<=2.28.0',
                      'python-dateutil==2.8.2', 'pandas==1.3.4', 'fastparquet==0.7.1'],
    dependency_links=['file:../common', 'file:../query', 'file:../testing'],
    entry_points={
        'console_scripts': [
            'dataplattform=dataplattform.cli:main',
        ],
    },
    zip_safe=False)

from setuptools import setup, find_packages

setup(
    name='dataplattform_api_common_modules',
    packages=find_packages('.'),
    install_requires=['sqlparse==0.4.2', 'pandas==1.1.5', 'cachetools==4.2.4'],
    zip_safe=False)

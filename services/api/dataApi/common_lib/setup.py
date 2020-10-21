from setuptools import setup, find_packages

setup(
    name='dataplattform_api_common_modules',
    packages=find_packages('.'),
    install_requires=['sqlparse', 'pandas', 'cachetools'],
    zip_safe=False)

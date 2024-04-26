#!/usr/bin/env python
from json import loads
from setuptools import setup, find_packages

setup(
    name='advertrappr',
    version='0.0.1',
    description='',
    url='https://github.com/dsp-shp/advertrappr',
    author='Ivan Derkach',
    author_email='dsp_shp@icloud.com',
    license='MIT License',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "advertrappr = advertrappr.main:cli",
        ],
    },
    install_requires=open('requirements.txt').read().splitlines(),
)

#!/usr/bin/env python

from setuptools import setup

setup(
    name='Tromegle',
    version='0.1.0 alpha',
    author='Louis Thibault',
    author_email='',
    packages=['tromegle'],
    include_package_data=True,
    install_requires=['Twisted>=11.1.0'],
    url='https://github.com/louist87/tromegle',
    license='Creative Commons BY-NC-SA 3.0',
    description='Troll strangers!',
    long_description=open('README.md').read()
)

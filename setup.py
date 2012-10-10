#!/usr/bin/env python

from setuptools import setup

setup(
    name='tromegle',
    version='0.1.1b alpha',
    author='Louis Thibault',
    author_email='',
    packages=['tromegle'],
    include_package_data=True,
    install_requires=['Twisted>=11.1.0', 'blessings>=1.5'],
    url='https://github.com/louist87/tromegle',
    license='GPL 3.0',
    description='Troll strangers!',
    keywords=["omegle", "trolling"],
    long_description=open('README.md').read()
)

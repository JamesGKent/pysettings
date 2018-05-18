#!/usr/bin/env python

from setuptools import setup
# To use a consistent encoding
from codecs import open
from os import path

VERSION = "1.0.0"

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pysettings',
    version=VERSION,
    description='simple settings library.',
    long_description=long_description,
	long_description_content_type='text/markdown',
    author='James Kent',
    url='https://github.com/JamesGKent/pysettings',
    download_url='https://github.com/JamesGKent/pysettings',
    py_modules=['pysettings'],
    license='MIT License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='settings',
    install_requires=['setuptools'],
)
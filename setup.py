#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='amadash',
    version='1.0.0',
    description='Amazon Dash button monitor',
    author='Igor Partola',
    author_email='igor@igorpartola.com',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'conf', 'tmp']),
    entry_points={
        'console_scripts': [
            'amadash = amadash.main:main',
            'amadash-discover = amadash.discover:main',
        ]
    },
    #install_requires=['pypcap'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
)

#!/usr/bin/env python

from setuptools import setup

setup(name='elvis',
      version='0.1.2',
      author='Sergio Oramas',
      author_email='sergio DOT oramas AT upf DOT edu',
      license='MIT',
      description='Framework to homogenize and combine the output of different entity linking tools.',
      packages=['elvis'],
      install_requires=[
		'nltk',
		'requests',
		'networkx',
		'numpy'
      ],
)


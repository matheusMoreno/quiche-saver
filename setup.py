# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='Quiche Saver Bot',
    version='0.1.0',
    description='',
    long_description=readme,
    author='Matheus Moreno',
    author_email='matheus.moreno@poli.ufrj.br',
    url='https://github.com/matheusMoreno/quichesaver',
    license=license,
    packages=find_packages(exclude=())
)

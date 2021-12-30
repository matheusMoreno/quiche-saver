# -*- coding: utf-8 -*-

"""Setup config for quichesaver."""

from setuptools import setup, find_packages


with open('README.md', encoding='utf-8') as f:
    readme = f.read()

with open('LICENSE', encoding='utf-8') as f:
    my_license = f.read()

setup(
    name='Quiche Saver Bot',
    version='0.1.0',
    description='Telegram bot that monitors products and informs when they '
    'are back in stock or below a desired price ',
    long_description=readme,
    author='Matheus Moreno',
    author_email='matheus.moreno@poli.ufrj.br',
    url='https://github.com/matheusMoreno/quichesaver',
    license=my_license,
    packages=find_packages(exclude=())
)

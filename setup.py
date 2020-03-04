import os
from setuptools import setup


def contents(filename):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename)) as fp:
        return fp.read()


setup(
    name='sqlalchemy-json',
    version='0.4.0',
    author='Elmer de Looff',
    author_email='elmer.delooff@gmail.com',
    description='JSON type with nested change tracking for SQLAlchemy',
    long_description=contents('README.rst'),
    keywords='sqlalchemy json mutable',
    license='BSD',
    url='https://github.com/edelooff/sqlalchemy-json',
    packages=['sqlalchemy_json'],
    install_requires=[
        'six',
        'sqlalchemy>=0.7'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Database'])

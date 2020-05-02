# -*- coding: utf-8 -*-

"""Simple security for Flask apps."""

from setuptools import find_packages, setup

readme = open('README.rst').read()

tests_require = [
    'Flask-CLI>=0.4.0',
    'Flask-Mongoengine>=0.7.0',
    'Flask-Peewee>=0.6.5',
    'Flask-SQLAlchemy>=1.0',
    'bcrypt>=1.0.2',
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'mock>=1.3.0',
    'mongoengine>=0.10.0',
    'pony>=0.7.1',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=2.4.0',
    'pytest-flakes>=1.0.1',
    'pytest-pep8>=1.0.6',
    'pytest-translations>=2.0.0',
    'pytest>=3.3.0',
    'sqlalchemy>=0.8.0',
]

extras_require = {
    'docs': [
        'Flask-Sphinx-Themes>=1.0.1',
        'Sphinx>=1.4.2',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask>=0.11',
    'Flask-Login>=0.3.0',
    'Flask-Mail>=0.7.3',
    'Flask-Principal>=0.3.3',
    'Flask-WTF>=0.13.1',
    'Flask-BabelEx>=0.9.3',
    'itsdangerous>=0.21',
    'passlib>=1.7',
    'cachetools>=3.1.0',
]

packages = find_packages()

setup(
    name='Flask-Security',
    version='3.0.0',
    description=__doc__,
    long_description=readme,
    keywords='flask security',
    license='MIT',
    author='Matt Wright',
    author_email='matt@nobien.net',
    url='https://github.com/mattupstate/flask-security',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Development Status :: 4 - Beta',
    ],
)

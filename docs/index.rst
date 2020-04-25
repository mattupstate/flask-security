Flask-Security
==============

Flask-Security allows you to quickly add common security mechanisms to your
Flask application. They include:

1. Session based authentication
2. Role management
3. Password hashing
4. Basic HTTP authentication
5. Token based authentication
6. Token based account activation (optional)
7. Token based password recovery / resetting (optional)
8. Two-factor authentication (optional)
9. User registration (optional)
10. Login tracking (optional)
11. JSON/Ajax Support

Many of these features are made possible by integrating various Flask extensions
and libraries. They include:

1. `Flask-Login <https://flask-login.readthedocs.org/en/latest/>`_
2. `Flask-Mail <http://packages.python.org/Flask-Mail/>`_
3. `Flask-Principal <http://packages.python.org/Flask-Principal/>`_
4. `Flask-WTF <http://packages.python.org/Flask-WTF/>`_
5. `itsdangerous <http://packages.python.org/itsdangerous/>`_
6. `passlib <http://packages.python.org/passlib/>`_
8. `onetimepass <https://pypi.python.org/pypi/onetimepass/>`_
9. `PyQRCode <https://pypi.python.org/pypi/PyQRCode/>`_

Additionally, it assumes you'll be using a common library for your database
connections and model definitions. Flask-Security supports the following Flask
extensions out of the box for data persistence:

1. `Flask-SQLAlchemy <http://pypi.python.org/pypi/flask-sqlalchemy/>`_
2. `Flask-MongoEngine <http://pypi.python.org/pypi/flask-mongoengine/>`_
3. `Flask-Peewee <http://pypi.python.org/pypi/flask-peewee/>`_
4. `PonyORM <http://pypi.python.org/pypi/pony/>`_


.. include:: contents.rst.inc

Two-factor Configurations
=========================

Two-factor authentication provides a second layer of security to any type of
login, requiring extra information or a secondary device to log in, in addition
to ones login credentials. The added feature includes the ability to add a
secondary authentication method using either via email, sms message, or Google
Authenticator.

The following code sample illustrates how to get started as quickly as
possible using SQLAlchemy and two-factor feature:

-  `Basic SQLAlchemy Application <#basic-sqlalchemy-application>`_

Basic SQLAlchemy Application
=============================

SQLAlchemy Install requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

     $ mkvirtualenv <your-app-name>
     $ pip install flask-security flask-sqlalchemy


Two-factor Application
~~~~~~~~~~~~~~~~~~~~~~

The following code sample illustrates how to get started as quickly as
possible using SQLAlchemy:

::

    from flask import Flask, current_app, render_template
    from flask_sqlalchemy import SQLAlchemy
    from flask_security import Security, SQLAlchemyUserDatastore, \
        UserMixin, RoleMixin, login_required


    # At top of file
    from flask_mail import Mail


    # Convenient references
    from werkzeug.datastructures import MultiDict
    from werkzeug.local import LocalProxy


    _security = LocalProxy(lambda: current_app.extensions['security'])

    _datastore = LocalProxy(lambda: _security.datastore)

    # Create app
    app = Flask(__name__)
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'super-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

    app.config['SECURITY_TWO_FACTOR_ENABLED_METHODS'] = ['mail',
      'google_authenticator']  # 'sms' also valid but requires an sms provider
    app.config["SECURITY_TWO_FACTOR"] = True
    app.config['SECURITY_TWO_FACTOR_RESCUE_MAIL'] = 'put_your_mail@gmail.com'
    app.config['SECURITY_TWO_FACTOR_URI_SERVICE_NAME'] = 'put_your_app_name'

    # Create database connection object
    db = SQLAlchemy(app)

    # Define models
    roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

    class Role(db.Model, RoleMixin):
      id = db.Column(db.Integer(), primary_key=True)
      name = db.Column(db.String(80), unique=True)
      description = db.Column(db.String(255))

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(255), unique=True)
        password = db.Column(db.String(255))
        active = db.Column(db.Boolean())
        confirmed_at = db.Column(db.DateTime())
        roles = db.relationship('Role', secondary=roles_users,
                                backref=db.backref('users', lazy='dynamic'))
        phone_number = db.Column(db.String(15))
        two_factor_primary_method = db.Column(db.String(140))
        totp_secret = db.Column(db.String(16))

    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    mail = Mail(app)

    # Create a user to test with
    @app.before_first_request
    def create_user():
        db.create_all()
        user_datastore.create_user(email='gal@lp.com', password='password', username='gal',
                               totp_secret=None, two_factor_primary_method=None)
        db.session.commit()

    # Views
    @app.route('/')
    @login_required
    def home():
        return render_template('index.html')

    if __name__ == '__main__':
        app.run()

Customizing Views
=================

Flask-Security bootstraps your application with various views for handling its
configured features to get you up and running as quickly as possible. However,
you'll probably want to change the way these views look to be more in line with
your application's visual design.


Views
-----

Flask-Security is packaged with a default template for each view it presents to
a user. Templates are located within a subfolder named ``security``. The
following is a list of view templates:

* `security/forgot_password.html`
* `security/login_user.html`
* `security/register_user.html`
* `security/reset_password.html`
* `security/change_password.html`
* `security/send_confirmation.html`
* `security/send_login.html`
* `security/two_factor_change_method_password_confirmation.html`
* `security/two_factor_choose_method.html`
* `security/two_factor_verify_code.html`

Overriding these templates is simple:

1. Create a folder named ``security`` within your application's templates folder
2. Create a template with the same name for the template you wish to override

You can also specify custom template file paths in the :doc:`configuration <configuration>`.

Each template is passed a template context object that includes the following,
including the objects/values that are passed to the template by the main
Flask application context processor:

* ``<template_name>_form``: A form object for the view
* ``security``: The Flask-Security extension object

To add more values to the template context, you can specify a context processor
for all views or a specific view. For example::

    security = Security(app, user_datastore)

    # This processor is added to all templates
    @security.context_processor
    def security_context_processor():
        return dict(hello="world")

    # This processor is added to only the register view
    @security.register_context_processor
    def security_register_processor():
        return dict(something="else")

The following is a list of all the available context processor decorators:

* ``context_processor``: All views
* ``forgot_password_context_processor``: Forgot password view
* ``login_context_processor``: Login view
* ``register_context_processor``: Register view
* ``reset_password_context_processor``: Reset password view
* ``change_password_context_processor``: Change password view
* ``send_confirmation_context_processor``: Send confirmation view
* ``send_login_context_processor``: Send login view


Forms
-----

All forms can be overridden. For each form used, you can specify a
replacement class. This allows you to add extra fields to the
register form or override validators::

    from flask_security.forms import RegisterForm
    from wtforms import StringField
    from wtforms.validators import DataRequired

    class ExtendedRegisterForm(RegisterForm):
        first_name = StringField('First Name', [DataRequired()])
        last_name = StringField('Last Name', [DataRequired()])

    security = Security(app, user_datastore,
             register_form=ExtendedRegisterForm)

For the ``register_form`` and ``confirm_register_form``, each field is
passed to the user model (as kwargs) when a user is created. In the
above case, the ``first_name`` and ``last_name`` fields are passed
directly to the model, so the model should look like::

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(255), unique=True)
        password = db.Column(db.String(255))
        first_name = db.Column(db.String(255))
        last_name = db.Column(db.String(255))

The following is a list of all the available form overrides:

* ``login_form``: Login form
* ``confirm_register_form``: Confirmable register form
* ``register_form``: Register form
* ``forgot_password_form``: Forgot password form
* ``reset_password_form``: Reset password form
* ``change_password_form``: Change password form
* ``send_confirmation_form``: Send confirmation form
* ``passwordless_login_form``: Passwordless login form
* ``two_factor_verify_code_form``: Two-factor code form
* ``two_factor_setup_form``: Two-factor setup form
* ``two_factor_change_method_verify_password_form``: Two-factor password form
* ``two_factor_rescue_form``: Two-factor help user form

Emails
------

Flask-Security is also packaged with a default template for each email that it
may send. Templates are located within the subfolder named ``security/email``.
The following is a list of email templates:

* `security/email/confirmation_instructions.html`
* `security/email/confirmation_instructions.txt`
* `security/email/login_instructions.html`
* `security/email/login_instructions.txt`
* `security/email/reset_instructions.html`
* `security/email/reset_instructions.txt`
* `security/email/reset_notice.html`
* `security/email/change_notice.txt`
* `security/email/change_notice.html`
* `security/email/reset_notice.txt`
* `security/email/welcome.html`
* `security/email/welcome.txt`
* `security/email/two_factor_instructions.html`
* `security/email/two_factor_instructions.txt`
* `security/email/two_factor_rescue.html`
* `security/email/two_factor_rescue.txt`

Overriding these templates is simple:

1. Create a folder named ``security`` within your application's templates folder
2. Create a folder named ``email`` within the ``security`` folder
3. Create a template with the same name for the template you wish to override

Each template is passed a template context object that includes values for any
links that are required in the email. If you require more values in the
templates, you can specify an email context processor with the
``mail_context_processor`` decorator. For example::

    security = Security(app, user_datastore)

    # This processor is added to all emails
    @security.mail_context_processor
    def security_mail_processor():
        return dict(hello="world")


Emails with Celery
------------------

Sometimes it makes sense to send emails via a task queue, such as `Celery`_.
To delay the sending of emails, you can use the ``@security.send_mail_task``
decorator like so::

    # Setup the task
    @celery.task
    def send_security_email(msg):
        # Use the Flask-Mail extension instance to send the incoming ``msg`` parameter
        # which is an instance of `flask_mail.Message`
        mail.send(msg)

    @security.send_mail_task
    def delay_security_email(msg):
        send_security_email.delay(msg)

If factory method is going to be used for initialization, use ``_SecurityState``
object returned by ``init_app`` method to initialize Celery tasks instead of using
``security.send_mail_task`` directly like so::

    from flask import Flask
    from flask_mail import Mail
    from flask_security import Security, SQLAlchemyUserDatastore
    from celery import Celery

    mail = Mail()
    security = Security()
    celery = Celery()

    def create_app(config):
        """Initialize Flask instance."""

        app = Flask(__name__)
        app.config.from_object(config)

        @celery.task
        def send_flask_mail(msg):
            mail.send(msg)

        mail.init_app(app)
        datastore = SQLAlchemyUserDatastore(db, User, Role)
        security_ctx = security.init_app(app, datastore)

        # Flexible way for defining custom mail sending task.
        @security_ctx.send_mail_task
        def delay_flask_security_mail(msg):
            send_flask_mail.delay(msg)

        # A shortcut.
        security_ctx.send_mail_task(send_flask_mail.delay)

        return app

Note that ``flask_mail.Message`` may not be serialized as an argument passed to
Celery. The practical way with custom serialization may look like so::

    @celery.task
    def send_flask_mail(**kwargs):
            mail.send(Message(**kwargs))

    @security_ctx.send_mail_task
    def delay_flask_security_mail(msg):
        send_flask_mail.delay(subject=msg.subject, sender=msg.sender,
                              recipients=msg.recipients, body=msg.body,
                              html=msg.html)

.. _Celery: http://www.celeryproject.org/


Custom send_mail method
-----------------------

It's also possible to completely override the ``security.send_mail`` method to
implement your own logic.

For example, you might want to use an alternative email library like `Flask-Emails`:

    from flask import Flask
    from flask_security import Security, SQLAlchemyUserDatastore
    from flask_emails import Message

    security = Security()

    def create_app(config):
        """Initialize Flask instance."""

        app = Flask(__name__)
        app.config.from_object(config)

        def custom_send_mail(subject, recipient, template, **context):
            ctx = ('security/email', template)
            message = Message(
                subject=subject,
                html=_security.render_template('%s/%s.html' % ctx, **context))
            message.send(mail_to=[recipient])

        datastore = SQLAlchemyUserDatastore(db, User, Role)
        security_ctx.send_mail = custom_send_mail

        return app

.. note::

    The above ``security.send_mail_task`` override will be useless if you
    override the entire ``send_mail`` method.


Authorization with OAuth2
-------------------------

Flask-Security can be set up to co-operate with `Flask-OAuthlib`_,
by implementing a custom request loader that authorizes a user based
either on a `Bearer` token in the HTTP `Authorization` header, or on the
Flask-Security standard authorization logic::

    from flask_oauthlib.provider import OAuth2Provider
    from flask_security import AnonymousUser
    from flask_security.core import (
        _user_loader as _flask_security_user_loader,
        _request_loader as _flask_security_request_loader)
    from flask_security.utils import config_value as security_config_value

    oauth = OAuth2Provider(app)

    def _request_loader(request):
        """
        Load user from OAuth2 Authentication header or using
        Flask-Security's request loader.
        """
        user = None

        if hasattr(request, 'oauth'):
            user = request.oauth.user
        else:
            # Need this try stmt in case oauthlib sometimes throws:
            # AttributeError: dict object has no attribute startswith
            try:
                is_valid, oauth_request = oauth.verify_request(scopes=[])
                if is_valid:
                    user = oauth_request.user
            except AttributeError:
                pass

        if not user:
            user = _flask_security_request_loader(request)

        return user

    def _get_login_manager(app, anonymous_user):
        """Prepare a login manager for Flask-Security to use."""
        login_manager = LoginManager()

        login_manager.anonymous_user = anonymous_user or AnonymousUser
        login_manager.login_view = '{0}.login'.format(
            security_config_value('BLUEPRINT_NAME', app=app))
        login_manager.user_loader(_flask_security_user_loader)
        login_manager.request_loader(_request_loader)

        if security_config_value('FLASH_MESSAGES', app=app):
            (login_manager.login_message,
             login_manager.login_message_category) = (
                security_config_value('MSG_LOGIN', app=app))
            (login_manager.needs_refresh_message,
             login_manager.needs_refresh_message_category) = (
                security_config_value('MSG_REFRESH', app=app))
        else:
            login_manager.login_message = None
            login_manager.needs_refresh_message = None

        login_manager.init_app(app)
        return login_manager

    security = Security(
        app, user_datastore,
        login_manager=_get_login_manager(app, anonymous_user=None))


.. _Flask-OAuthlib: https://flask-oauthlib.readthedocs.io/

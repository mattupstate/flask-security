# -*- coding: utf-8 -*-
"""
    flask_security.core
    ~~~~~~~~~~~~~~~~~~~

    Flask-Security core module

    :copyright: (c) 2012 by Matt Wright.
    :copyright: (c) 2017 by CERN.
    :copyright: (c) 2017 by ETH Zurich, Swiss Data Science Center.
    :license: MIT, see LICENSE for more details.
"""

from datetime import datetime

import pkg_resources
from flask import current_app, render_template
from flask_babelex import Domain
from flask_login import AnonymousUserMixin, LoginManager
from flask_login import UserMixin as BaseUserMixin
from flask_login import current_user
from flask_principal import Identity, Principal, RoleNeed, UserNeed, \
    identity_loaded
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext
from werkzeug.datastructures import ImmutableList
from werkzeug.local import LocalProxy

from .forms import ChangePasswordForm, ConfirmRegisterForm, \
    ForgotPasswordForm, LoginForm, PasswordlessLoginForm, RegisterForm, \
    ResetPasswordForm, SendConfirmationForm
from .utils import _
from .utils import config_value as cv
from .utils import get_config, hash_data, localize_callback, send_mail, \
    string_types, url_for_security, verify_and_update_password, verify_hash
from .views import create_blueprint

# Convenient references
_security = LocalProxy(lambda: current_app.extensions['security'])


#: Default Flask-Security configuration
_default_config = {
    'BLUEPRINT_NAME': 'security',
    'CLI_ROLES_NAME': 'roles',
    'CLI_USERS_NAME': 'users',
    'URL_PREFIX': None,
    'SUBDOMAIN': None,
    'FLASH_MESSAGES': True,
    'I18N_DOMAIN': 'flask_security',
    'I18N_DIRNAME': pkg_resources.resource_filename(
        'flask_security', 'translations'),
    'PASSWORD_HASH': 'bcrypt',
    'PASSWORD_SALT': None,
    'PASSWORD_SINGLE_HASH': {
        'django_argon2',
        'django_bcrypt_sha256',
        'django_pbkdf2_sha256',
        'django_pbkdf2_sha1',
        'django_bcrypt',
        'django_salted_md5',
        'django_salted_sha1',
        'django_des_crypt',
        'plaintext',
    },
    'LOGIN_URL': '/login',
    'LOGOUT_URL': '/logout',
    'REGISTER_URL': '/register',
    'RESET_URL': '/reset',
    'CHANGE_URL': '/change',
    'CONFIRM_URL': '/confirm',
    'POST_LOGIN_VIEW': '/',
    'POST_LOGOUT_VIEW': '/',
    'CONFIRM_ERROR_VIEW': None,
    'POST_REGISTER_VIEW': None,
    'POST_CONFIRM_VIEW': None,
    'POST_RESET_VIEW': None,
    'POST_CHANGE_VIEW': None,
    'UNAUTHORIZED_VIEW': None,
    'FORGOT_PASSWORD_TEMPLATE': 'security/forgot_password.html',
    'LOGIN_USER_TEMPLATE': 'security/login_user.html',
    'REGISTER_USER_TEMPLATE': 'security/register_user.html',
    'RESET_PASSWORD_TEMPLATE': 'security/reset_password.html',
    'CHANGE_PASSWORD_TEMPLATE': 'security/change_password.html',
    'SEND_CONFIRMATION_TEMPLATE': 'security/send_confirmation.html',
    'SEND_LOGIN_TEMPLATE': 'security/send_login.html',
    'CONFIRMABLE': False,
    'REGISTERABLE': False,
    'RECOVERABLE': False,
    'TRACKABLE': False,
    'PASSWORDLESS': False,
    'CHANGEABLE': False,
    'SEND_REGISTER_EMAIL': True,
    'SEND_PASSWORD_CHANGE_EMAIL': True,
    'SEND_PASSWORD_RESET_EMAIL': True,
    'SEND_PASSWORD_RESET_NOTICE_EMAIL': True,
    'LOGIN_WITHIN': '1 days',
    'CONFIRM_EMAIL_WITHIN': '5 days',
    'RESET_PASSWORD_WITHIN': '5 days',
    'LOGIN_WITHOUT_CONFIRMATION': False,
    'EMAIL_SENDER': LocalProxy(lambda: current_app.config.get(
        'MAIL_DEFAULT_SENDER', 'no-reply@localhost'
    )),
    'TOKEN_AUTHENTICATION_KEY': 'auth_token',
    'TOKEN_AUTHENTICATION_HEADER': 'Authentication-Token',
    'TOKEN_MAX_AGE': None,
    'CONFIRM_SALT': 'confirm-salt',
    'RESET_SALT': 'reset-salt',
    'LOGIN_SALT': 'login-salt',
    'CHANGE_SALT': 'change-salt',
    'REMEMBER_SALT': 'remember-salt',
    'DEFAULT_REMEMBER_ME': False,
    'DEFAULT_HTTP_AUTH_REALM': _('Login Required'),
    'EMAIL_SUBJECT_REGISTER': _('Welcome'),
    'EMAIL_SUBJECT_CONFIRM': _('Please confirm your email'),
    'EMAIL_SUBJECT_PASSWORDLESS': _('Login instructions'),
    'EMAIL_SUBJECT_PASSWORD_NOTICE': _('Your password has been reset'),
    'EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE': _(
                                    'Your password has been changed'),
    'EMAIL_SUBJECT_PASSWORD_RESET': _('Password reset instructions'),
    'EMAIL_PLAINTEXT': True,
    'EMAIL_HTML': True,
    'USER_IDENTITY_ATTRIBUTES': ['email'],
    'PASSWORD_SCHEMES': [
        'bcrypt',
        'des_crypt',
        'pbkdf2_sha256',
        'pbkdf2_sha512',
        'sha256_crypt',
        'sha512_crypt',
        # And always last one...
        'plaintext'
    ],
    'DEPRECATED_PASSWORD_SCHEMES': ['auto'],
    'HASHING_SCHEMES': [
        'sha256_crypt',
        'hex_md5',
    ],
    'DEPRECATED_HASHING_SCHEMES': ['hex_md5'],
    'DATETIME_FACTORY': datetime.utcnow,
}

#: Default Flask-Security messages
_default_messages = {
    'UNAUTHORIZED': (
        _('You do not have permission to view this resource.'), 'error'),
    'CONFIRM_REGISTRATION': (
        _('Thank you. Confirmation instructions '
          'have been sent to %(email)s.'),
        'success'),
    'EMAIL_CONFIRMED': (
        _('Thank you. Your email has been confirmed.'), 'success'),
    'ALREADY_CONFIRMED': (
        _('Your email has already been confirmed.'), 'info'),
    'INVALID_CONFIRMATION_TOKEN': (
        _('Invalid confirmation token.'), 'error'),
    'EMAIL_ALREADY_ASSOCIATED': (
        _('%(email)s is already associated with an account.'), 'error'),
    'PASSWORD_MISMATCH': (
        _('Password does not match'), 'error'),
    'RETYPE_PASSWORD_MISMATCH': (
        _('Passwords do not match'), 'error'),
    'INVALID_REDIRECT': (
        _('Redirections outside the domain are forbidden'), 'error'),
    'PASSWORD_RESET_REQUEST': (
        _('Instructions to reset your password have been sent to %(email)s.'),
        'info'),
    'PASSWORD_RESET_EXPIRED': (
        _('You did not reset your password within %(within)s. '
          'New instructions have been sent to %(email)s.'), 'error'),
    'INVALID_RESET_PASSWORD_TOKEN': (
        _('Invalid reset password token.'), 'error'),
    'CONFIRMATION_REQUIRED': (
        _('Email requires confirmation.'), 'error'),
    'CONFIRMATION_REQUEST': (
        _('Confirmation instructions have been sent to %(email)s.'), 'info'),
    'CONFIRMATION_EXPIRED': (
        _('You did not confirm your email within %(within)s. '
          'New instructions to confirm your email have been sent '
          'to %(email)s.'), 'error'),
    'LOGIN_EXPIRED': (
        _('You did not login within %(within)s. New instructions to login '
          'have been sent to %(email)s.'), 'error'),
    'LOGIN_EMAIL_SENT': (
        _('Instructions to login have been sent to %(email)s.'), 'success'),
    'INVALID_LOGIN_TOKEN': (
        _('Invalid login token.'), 'error'),
    'DISABLED_ACCOUNT': (
        _('Account is disabled.'), 'error'),
    'EMAIL_NOT_PROVIDED': (
        _('Email not provided'), 'error'),
    'INVALID_EMAIL_ADDRESS': (
        _('Invalid email address'), 'error'),
    'PASSWORD_NOT_PROVIDED': (
        _('Password not provided'), 'error'),
    'PASSWORD_NOT_SET': (
        _('No password is set for this user'), 'error'),
    'PASSWORD_INVALID_LENGTH': (
        _('Password must be at least 6 characters'), 'error'),
    'USER_DOES_NOT_EXIST': (
        _('Specified user does not exist'), 'error'),
    'INVALID_PASSWORD': (
        _('Invalid password'), 'error'),
    'PASSWORDLESS_LOGIN_SUCCESSFUL': (
        _('You have successfully logged in.'), 'success'),
    'FORGOT_PASSWORD': (
        _('Forgot password?'), 'info'),
    'PASSWORD_RESET': (
        _('You successfully reset your password and you have been logged in '
          'automatically.'), 'success'),
    'PASSWORD_IS_THE_SAME': (
        _('Your new password must be different than your previous password.'),
        'error'),
    'PASSWORD_CHANGE': (
        _('You successfully changed your password.'), 'success'),
    'LOGIN': (
        _('Please log in to access this page.'), 'info'),
    'REFRESH': (
        _('Please reauthenticate to access this page.'), 'info'),
}

_default_forms = {
    'login_form': LoginForm,
    'confirm_register_form': ConfirmRegisterForm,
    'register_form': RegisterForm,
    'forgot_password_form': ForgotPasswordForm,
    'reset_password_form': ResetPasswordForm,
    'change_password_form': ChangePasswordForm,
    'send_confirmation_form': SendConfirmationForm,
    'passwordless_login_form': PasswordlessLoginForm,
}


def _user_loader(user_id):
    return _security.datastore.find_user(id=user_id)


def _request_loader(request):
    header_key = _security.token_authentication_header
    args_key = _security.token_authentication_key
    header_token = request.headers.get(header_key, None)
    token = request.args.get(args_key, header_token)
    if request.is_json:
        data = request.get_json(silent=True) or {}
        if isinstance(data, dict):
            token = data.get(args_key, token)

    try:
        data = _security.remember_token_serializer.loads(
            token, max_age=_security.token_max_age)
        user = _security.datastore.find_user(id=data[0])
        if user and verify_hash(data[1], user.password):
            return user
    except:
        pass
    return _security.login_manager.anonymous_user()


def _identity_loader():
    if not isinstance(current_user._get_current_object(), AnonymousUserMixin):
        identity = Identity(current_user.id)
        return identity


def _on_identity_loaded(sender, identity):
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    for role in getattr(current_user, 'roles', []):
        identity.provides.add(RoleNeed(role.name))

    identity.user = current_user


def _get_login_manager(app, anonymous_user):
    lm = LoginManager()
    lm.anonymous_user = anonymous_user or AnonymousUser
    lm.localize_callback = localize_callback
    lm.login_view = '%s.login' % cv('BLUEPRINT_NAME', app=app)
    lm.user_loader(_user_loader)
    lm.request_loader(_request_loader)

    if cv('FLASH_MESSAGES', app=app):
        lm.login_message, lm.login_message_category = cv('MSG_LOGIN', app=app)
        lm.needs_refresh_message, lm.needs_refresh_message_category = cv(
            'MSG_REFRESH', app=app)
    else:
        lm.login_message = None
        lm.needs_refresh_message = None

    lm.init_app(app)
    return lm


def _get_principal(app):
    p = Principal(app, use_sessions=False)
    p.identity_loader(_identity_loader)
    return p


def _get_pwd_context(app):
    pw_hash = cv('PASSWORD_HASH', app=app)
    schemes = cv('PASSWORD_SCHEMES', app=app)
    deprecated = cv('DEPRECATED_PASSWORD_SCHEMES', app=app)
    if pw_hash not in schemes:
        allowed = (', '.join(schemes[:-1]) + ' and ' + schemes[-1])
        raise ValueError(
            "Invalid password hashing scheme %r. Allowed values are %s" %
            (pw_hash, allowed))
    return CryptContext(
        schemes=schemes,
        default=pw_hash,
        deprecated=deprecated)


def _get_i18n_domain(app):
    return Domain(
        dirname=cv('I18N_DIRNAME', app=app),
        domain=cv('I18N_DOMAIN', app=app)
    )


def _get_hashing_context(app):
    schemes = cv('HASHING_SCHEMES', app=app)
    deprecated = cv('DEPRECATED_HASHING_SCHEMES', app=app)
    return CryptContext(
        schemes=schemes,
        deprecated=deprecated)


def _get_serializer(app, name):
    secret_key = app.config.get('SECRET_KEY')
    salt = app.config.get('SECURITY_%s_SALT' % name.upper())
    return URLSafeTimedSerializer(secret_key=secret_key, salt=salt)


def _get_state(app, datastore, anonymous_user=None, **kwargs):
    for key, value in get_config(app).items():
        kwargs[key.lower()] = value

    kwargs.update(dict(
        app=app,
        datastore=datastore,
        principal=_get_principal(app),
        pwd_context=_get_pwd_context(app),
        hashing_context=_get_hashing_context(app),
        i18n_domain=_get_i18n_domain(app),
        remember_token_serializer=_get_serializer(app, 'remember'),
        login_serializer=_get_serializer(app, 'login'),
        reset_serializer=_get_serializer(app, 'reset'),
        confirm_serializer=_get_serializer(app, 'confirm'),
        _context_processors={},
        _send_mail_task=None,
        _unauthorized_callback=None
    ))

    if 'login_manager' not in kwargs:
        kwargs['login_manager'] = _get_login_manager(
            app, anonymous_user)

    for key, value in _default_forms.items():
        if key not in kwargs or not kwargs[key]:
            kwargs[key] = value

    return _SecurityState(**kwargs)


def _context_processor():
    return dict(url_for_security=url_for_security, security=_security)


class RoleMixin(object):
    """Mixin for `Role` model definitions"""

    def __eq__(self, other):
        return (self.name == other or
                self.name == getattr(other, 'name', None))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)


class UserMixin(BaseUserMixin):
    """Mixin for `User` model definitions"""

    @property
    def is_active(self):
        """Returns `True` if the user is active."""
        return self.active

    def get_auth_token(self):
        """Returns the user's authentication token."""
        data = [str(self.id), hash_data(self.password)]
        return _security.remember_token_serializer.dumps(data)

    def has_role(self, role):
        """Returns `True` if the user identifies with the specified role.

        :param role: A role name or `Role` instance"""
        if isinstance(role, string_types):
            return role in (role.name for role in self.roles)
        else:
            return role in self.roles

    def get_security_payload(self):
        """Serialize user object as response payload."""
        return {'id': str(self.id)}

    def verify_and_update_password(self, password):
        """Verify and update user password using configured hash."""
        return verify_and_update_password(password, self)


class AnonymousUser(AnonymousUserMixin):
    """AnonymousUser definition"""

    def __init__(self):
        self.roles = ImmutableList()

    def has_role(self, *args):
        """Returns `False`"""
        return False


class _SecurityState(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key.lower(), value)

    def _add_ctx_processor(self, endpoint, fn):
        group = self._context_processors.setdefault(endpoint, [])
        fn not in group and group.append(fn)

    def _run_ctx_processor(self, endpoint):
        rv = {}
        for g in [None, endpoint]:
            for fn in self._context_processors.setdefault(g, []):
                rv.update(fn())
        return rv

    def context_processor(self, fn):
        self._add_ctx_processor(None, fn)

    def forgot_password_context_processor(self, fn):
        self._add_ctx_processor('forgot_password', fn)

    def login_context_processor(self, fn):
        self._add_ctx_processor('login', fn)

    def register_context_processor(self, fn):
        self._add_ctx_processor('register', fn)

    def reset_password_context_processor(self, fn):
        self._add_ctx_processor('reset_password', fn)

    def change_password_context_processor(self, fn):
        self._add_ctx_processor('change_password', fn)

    def send_confirmation_context_processor(self, fn):
        self._add_ctx_processor('send_confirmation', fn)

    def send_login_context_processor(self, fn):
        self._add_ctx_processor('send_login', fn)

    def mail_context_processor(self, fn):
        self._add_ctx_processor('mail', fn)

    def send_mail_task(self, fn):
        self._send_mail_task = fn

    def unauthorized_handler(self, fn):
        self._unauthorized_callback = fn


class Security(object):
    """The :class:`Security` class initializes the Flask-Security extension.

    :param app: The application.
    :param datastore: An instance of a user datastore.
    :param register_blueprint: to register the Security blueprint or not.
    :param login_form: set form for the login view
    :param register_form: set form for the register view
    :param confirm_register_form: set form for the confirm register view
    :param forgot_password_form: set form for the forgot password view
    :param reset_password_form: set form for the reset password view
    :param change_password_form: set form for the change password view
    :param send_confirmation_form: set form for the send confirmation view
    :param passwordless_login_form: set form for the passwordless login view
    :param anonymous_user: class to use for anonymous user
    """

    def __init__(self, app=None, datastore=None, register_blueprint=True,
                 **kwargs):
        self.app = app
        self._datastore = datastore
        self._register_blueprint = register_blueprint
        self._kwargs = kwargs

        self._state = None  # set by init_app
        if app is not None and datastore is not None:
            self._state = self.init_app(
                app,
                datastore,
                register_blueprint=register_blueprint,
                **kwargs)

    def init_app(self, app, datastore=None, register_blueprint=None, **kwargs):
        """Initializes the Flask-Security extension for the specified
        application and datastore implementation.

        :param app: The application.
        :param datastore: An instance of a user datastore.
        :param register_blueprint: to register the Security blueprint or not.
        """
        self.app = app

        if datastore is None:
            datastore = self._datastore

        if register_blueprint is None:
            register_blueprint = self._register_blueprint

        for key, value in self._kwargs.items():
            kwargs.setdefault(key, value)

        for key, value in _default_config.items():
            app.config.setdefault('SECURITY_' + key, value)

        for key, value in _default_messages.items():
            app.config.setdefault('SECURITY_MSG_' + key, value)

        identity_loaded.connect_via(app)(_on_identity_loaded)

        self._state = state = _get_state(app, datastore, **kwargs)

        if register_blueprint:
            app.register_blueprint(create_blueprint(state, __name__))
            app.context_processor(_context_processor)

        @app.before_first_request
        def _register_i18n():
            if '_' not in app.jinja_env.globals:
                app.jinja_env.globals['_'] = state.i18n_domain.gettext

        state.render_template = self.render_template
        state.send_mail = self.send_mail
        app.extensions['security'] = state

        if hasattr(app, 'cli'):
            from .cli import users, roles
            if state.cli_users_name:
                app.cli.add_command(users, state.cli_users_name)
            if state.cli_roles_name:
                app.cli.add_command(roles, state.cli_roles_name)

        return state

    def render_template(self, *args, **kwargs):
        return render_template(*args, **kwargs)

    def send_mail(self, *args, **kwargs):
        return send_mail(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._state, name, None)

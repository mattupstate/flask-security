# -*- coding: utf-8 -*-
"""
    test_emails
    ~~~~~~~~~~~

    Email functionality tests
"""

import hashlib

import pytest
from utils import authenticate, init_app_with_options, populate_data

from flask_security import Security
from flask_security.forms import ChangePasswordForm, ConfirmRegisterForm, \
    ForgotPasswordForm, LoginForm, PasswordField, PasswordlessLoginForm, \
    RegisterForm, ResetPasswordForm, SendConfirmationForm, StringField, \
    email_required, email_validator, valid_user_email
from flask_security.utils import capture_reset_password_requests, \
    encode_string, hash_data, string_types, verify_hash


@pytest.mark.recoverable()
def test_async_email_task(app, client):
    app.mail_sent = False

    @app.security.send_mail_task
    def send_email(msg):
        app.mail_sent = True

    client.post('/reset', data=dict(email='matt@lp.com'))
    assert app.mail_sent is True


def test_not_logoutable(app, sqlalchemy_datastore):
    app.config['SECURITY_LOGOUTABLE'] = False
    app.security = Security(app, datastore=sqlalchemy_datastore)
    client = app.test_client()
    e = 'matt@lp.com'
    authenticate(client, email=e)
    response = client.get('/logout')
    assert response.status_code == 404


@pytest.mark.registerable()
@pytest.mark.recoverable()
@pytest.mark.changeable()
def test_basic_custom_forms(app, sqlalchemy_datastore):
    class MyLoginForm(LoginForm):
        email = StringField('My Login Email Address Field')

    class MyRegisterForm(RegisterForm):
        email = StringField('My Register Email Address Field')

    class MyForgotPasswordForm(ForgotPasswordForm):
        email = StringField(
            'My Forgot Email Address Field',
            validators=[
                email_required,
                email_validator,
                valid_user_email])

    class MyResetPasswordForm(ResetPasswordForm):
        password = StringField('My Reset Password Field')

    class MyChangePasswordForm(ChangePasswordForm):
        password = PasswordField('My Change Password Field')

    app.security = Security(app,
                            datastore=sqlalchemy_datastore,
                            login_form=MyLoginForm,
                            register_form=MyRegisterForm,
                            forgot_password_form=MyForgotPasswordForm,
                            reset_password_form=MyResetPasswordForm,
                            change_password_form=MyChangePasswordForm)

    populate_data(app)
    client = app.test_client()

    response = client.get('/login')
    assert b'My Login Email Address Field' in response.data

    response = client.get('/register')
    assert b'My Register Email Address Field' in response.data

    response = client.get('/reset')
    assert b'My Forgot Email Address Field' in response.data

    with capture_reset_password_requests() as requests:
        response = client.post('/reset', data=dict(email='matt@lp.com'))

    token = requests[0]['token']
    response = client.get('/reset/' + token)
    assert b'My Reset Password Field' in response.data

    authenticate(client)

    response = client.get('/change')
    assert b'My Change Password Field' in response.data


@pytest.mark.registerable()
@pytest.mark.confirmable()
def test_confirmable_custom_form(app, sqlalchemy_datastore):
    app.config['SECURITY_REGISTERABLE'] = True
    app.config['SECURITY_CONFIRMABLE'] = True

    class MyRegisterForm(ConfirmRegisterForm):
        email = StringField('My Register Email Address Field')

    class MySendConfirmationForm(SendConfirmationForm):
        email = StringField('My Send Confirmation Email Address Field')

    app.security = Security(app,
                            datastore=sqlalchemy_datastore,
                            send_confirmation_form=MySendConfirmationForm,
                            confirm_register_form=MyRegisterForm)

    client = app.test_client()

    response = client.get('/register')
    assert b'My Register Email Address Field' in response.data

    response = client.get('/confirm')
    assert b'My Send Confirmation Email Address Field' in response.data


def test_passwordless_custom_form(app, sqlalchemy_datastore):
    app.config['SECURITY_PASSWORDLESS'] = True

    class MyPasswordlessLoginForm(PasswordlessLoginForm):
        email = StringField('My Passwordless Email Address Field')

    app.security = Security(app,
                            datastore=sqlalchemy_datastore,
                            passwordless_login_form=MyPasswordlessLoginForm)

    client = app.test_client()

    response = client.get('/login')
    assert b'My Passwordless Email Address Field' in response.data


def test_addition_identity_attributes(app, sqlalchemy_datastore):
    init_app_with_options(app, sqlalchemy_datastore, **{
        'SECURITY_USER_IDENTITY_ATTRIBUTES': ('email', 'username')
    })
    client = app.test_client()
    response = authenticate(client, email='matt', follow_redirects=True)
    assert b'Hello matt@lp.com' in response.data


def test_flash_messages_off(app, sqlalchemy_datastore, get_message):
    init_app_with_options(app, sqlalchemy_datastore, **{
        'SECURITY_FLASH_MESSAGES': False
    })
    client = app.test_client()
    response = client.get('/profile')
    assert get_message('LOGIN') not in response.data


def test_invalid_hash_scheme(app, sqlalchemy_datastore, get_message):
    with pytest.raises(ValueError):
        init_app_with_options(app, sqlalchemy_datastore, **{
            'SECURITY_PASSWORD_HASH': 'bogus'
        })


def test_change_hash_type(app, sqlalchemy_datastore):
    init_app_with_options(app, sqlalchemy_datastore, **{
        'SECURITY_PASSWORD_HASH': 'plaintext',
        'SECURITY_PASSWORD_SALT': None,
        'SECURITY_PASSWORD_SCHEMES': ['bcrypt', 'plaintext']
    })

    app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
    app.config['SECURITY_PASSWORD_SALT'] = 'salty'

    app.security = Security(
        app,
        datastore=sqlalchemy_datastore,
        register_blueprint=False)

    client = app.test_client()

    response = client.post(
        '/login',
        data=dict(
            email='matt@lp.com',
            password='password'))
    assert response.status_code == 302

    response = client.get('/logout')

    response = client.post(
        '/login',
        data=dict(
            email='matt@lp.com',
            password='password'))
    assert response.status_code == 302


@pytest.mark.settings(
    hashing_schemes=['hex_md5'],
    deprecated_hashing_schemes=[],
)
@pytest.mark.parametrize('data', [
    u'hellö',
    b'hello',
])
def test_legacy_hash(in_app_context, data):
    legacy_hash = hashlib.md5(encode_string(data)).hexdigest()
    new_hash = hash_data(data)
    assert legacy_hash == new_hash


def test_hash_data(in_app_context):
    data = hash_data(b'hello')
    assert isinstance(data, string_types)
    data = hash_data(u'hellö')
    assert isinstance(data, string_types)


def test_verify_hash(in_app_context):
    data = hash_data(u'hellö')
    assert verify_hash(data, u'hellö') is True
    assert verify_hash(data, u'hello') is False

    legacy_data = hashlib.md5(encode_string(u'hellö')).hexdigest()
    assert verify_hash(legacy_data, u'hellö') is True
    assert verify_hash(legacy_data, u'hello') is False


@pytest.mark.settings(password_salt=u'öööööööööööööööööööööööööööööööööö',
                      password_hash='bcrypt')
def test_password_unicode_password_salt(client):
    response = authenticate(client)
    assert response.status_code == 302
    response = authenticate(client, follow_redirects=True)
    assert b'Hello matt@lp.com' in response.data


def test_set_unauthorized_handler(app, client):
    @app.security.unauthorized_handler
    def unauthorized():
        app.unauthorized_handler_set = True
        return 'unauthorized-handler-set', 401

    app.unauthorized_handler_set = False

    authenticate(client, "joe@lp.com")
    response = client.get("/admin", follow_redirects=True)

    assert app.unauthorized_handler_set is True
    assert b'unauthorized-handler-set' in response.data
    assert response.status_code == 401


@pytest.mark.registerable()
def test_custom_forms_via_config(app, sqlalchemy_datastore):
    class MyLoginForm(LoginForm):
        email = StringField('My Login Email Address Field')

    class MyRegisterForm(RegisterForm):
        email = StringField('My Register Email Address Field')

    app.config['SECURITY_LOGIN_FORM'] = MyLoginForm
    app.config['SECURITY_REGISTER_FORM'] = MyRegisterForm

    security = Security(datastore=sqlalchemy_datastore)
    security.init_app(app)

    client = app.test_client()

    response = client.get('/login')
    assert b'My Login Email Address Field' in response.data

    response = client.get('/register')
    assert b'My Register Email Address Field' in response.data


@pytest.mark.babel(False)
def test_without_babel(client):
    response = client.get('/login')
    assert b'Login' in response.data


def test_register_blueprint_flag(app, sqlalchemy_datastore):
    app.security = Security(app, datastore=Security, register_blueprint=False)
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code == 404


def test_loginable(app, sqlalchemy_datastore):
    app.security = Security(app, datastore=sqlalchemy_datastore)
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code == 200


def test_not_loginable(app, sqlalchemy_datastore):
    app.config['SECURITY_LOGINABLE'] = False
    app.security = Security(app, datastore=sqlalchemy_datastore)
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code == 404


def test_logoutable(app, sqlalchemy_datastore):
    app.security = Security(app, datastore=sqlalchemy_datastore)
    client = app.test_client()
    e = 'matt@lp.com'
    authenticate(client, email=e)
    response = client.get('/logout')
    assert response.status_code == 302

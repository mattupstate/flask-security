# -*- coding: utf-8 -*-
"""
    flask_security.forms
    ~~~~~~~~~~~~~~~~~~~~

    Flask-Security forms module

    :copyright: (c) 2012 by Matt Wright.
    :copyright: (c) 2017 by CERN.
    :license: MIT, see LICENSE for more details.
"""

import inspect

from flask import Markup, current_app, flash, request
from flask_login import current_user
from flask_wtf import FlaskForm as BaseForm
from speaklater import make_lazy_gettext
from wtforms import BooleanField, Field, HiddenField, PasswordField, \
    StringField, SubmitField, ValidationError, validators

from .confirmable import requires_confirmation
from .utils import _, _datastore, config_value, get_message, hash_password, \
    localize_callback, url_for_security, validate_redirect_url

lazy_gettext = make_lazy_gettext(lambda: localize_callback)

_default_field_labels = {
    'email': _('Email Address'),
    'password': _('Password'),
    'remember_me': _('Remember Me'),
    'login': _('Login'),
    'register': _('Register'),
    'send_confirmation': _('Resend Confirmation Instructions'),
    'recover_password': _('Recover Password'),
    'reset_password': _('Reset Password'),
    'retype_password': _('Retype Password'),
    'new_password': _('New Password'),
    'change_password': _('Change Password'),
    'send_login_link': _('Send Login Link')
}


class ValidatorMixin(object):

    @property
    def message(self):
        if self._templated:
            return get_message(self._message)[0]
        return self._message

    @message.setter
    def message(self, value):
        self._templated = value and value.isupper()
        self._message = value


class EqualTo(ValidatorMixin, validators.EqualTo):
    pass


class Required(ValidatorMixin, validators.DataRequired):
    pass


class Email(ValidatorMixin, validators.Email):
    pass


class Length(ValidatorMixin, validators.Length):
    pass


email_required = Required(message='EMAIL_NOT_PROVIDED')
email_validator = Email(message='INVALID_EMAIL_ADDRESS')
password_required = Required(message='PASSWORD_NOT_PROVIDED')
password_length = Length(min=6, max=128, message='PASSWORD_INVALID_LENGTH')


def get_form_field_label(key):
    return lazy_gettext(_default_field_labels.get(key, ''))


def unique_user_email(form, field):
    if _datastore.get_user(field.data) is not None:
        msg = get_message('EMAIL_ALREADY_ASSOCIATED', email=field.data)[0]
        raise ValidationError(msg)


def valid_user_email(form, field):
    form.user = _datastore.get_user(field.data)
    if form.user is None:
        raise ValidationError(get_message('USER_DOES_NOT_EXIST')[0])


class Form(BaseForm):
    def __init__(self, *args, **kwargs):
        if current_app.testing:
            self.TIME_LIMIT = None
        super(Form, self).__init__(*args, **kwargs)


class EmailFormMixin():
    email = StringField(
        get_form_field_label('email'),
        validators=[email_required, email_validator])


class UserEmailFormMixin():
    user = None
    email = StringField(
        get_form_field_label('email'),
        validators=[email_required, email_validator, valid_user_email])


class UniqueEmailFormMixin():
    email = StringField(
        get_form_field_label('email'),
        validators=[email_required, email_validator, unique_user_email])


class PasswordFormMixin():
    password = PasswordField(
        get_form_field_label('password'), validators=[password_required])


class NewPasswordFormMixin():
    password = PasswordField(
        get_form_field_label('password'),
        validators=[password_required, password_length])


class PasswordConfirmFormMixin():
    password_confirm = PasswordField(
        get_form_field_label('retype_password'),
        validators=[EqualTo('password', message='RETYPE_PASSWORD_MISMATCH'),
                    password_required])


class NextFormMixin():
    next = HiddenField()

    def validate_next(self, field):
        if field.data and not validate_redirect_url(field.data):
            field.data = ''
            flash(*get_message('INVALID_REDIRECT'))
            raise ValidationError(get_message('INVALID_REDIRECT')[0])


class RegisterFormMixin():
    submit = SubmitField(get_form_field_label('register'))

    def to_dict(form):
        def is_field_and_user_attr(member):
            return isinstance(member, Field) and \
                hasattr(_datastore.user_model, member.name)

        fields = inspect.getmembers(form, is_field_and_user_attr)
        return dict((key, value.data) for key, value in fields)


class SendConfirmationForm(Form, UserEmailFormMixin):
    """The default send confirmation form"""

    submit = SubmitField(get_form_field_label('send_confirmation'))

    def __init__(self, *args, **kwargs):
        super(SendConfirmationForm, self).__init__(*args, **kwargs)
        if request.method == 'GET':
            self.email.data = request.args.get('email', None)

    def validate(self):
        if not super(SendConfirmationForm, self).validate():
            return False
        if self.user.confirmed_at is not None:
            self.email.errors.append(get_message('ALREADY_CONFIRMED')[0])
            return False
        return True


class ForgotPasswordForm(Form, UserEmailFormMixin):
    """The default forgot password form"""

    submit = SubmitField(get_form_field_label('recover_password'))

    def validate(self):
        if not super(ForgotPasswordForm, self).validate():
            return False
        if requires_confirmation(self.user):
            self.email.errors.append(get_message('CONFIRMATION_REQUIRED')[0])
            return False
        return True


class PasswordlessLoginForm(Form, UserEmailFormMixin):
    """The passwordless login form"""

    submit = SubmitField(get_form_field_label('send_login_link'))

    def __init__(self, *args, **kwargs):
        super(PasswordlessLoginForm, self).__init__(*args, **kwargs)

    def validate(self):
        if not super(PasswordlessLoginForm, self).validate():
            return False
        if not self.user.is_active:
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False
        return True


class LoginForm(Form, NextFormMixin):
    """The default login form"""

    email = StringField(get_form_field_label('email'),
                        validators=[Required(message='EMAIL_NOT_PROVIDED')])
    password = PasswordField(get_form_field_label('password'),
                             validators=[password_required])
    remember = BooleanField(get_form_field_label('remember_me'))
    submit = SubmitField(get_form_field_label('login'))

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        if not self.next.data:
            self.next.data = request.args.get('next', '')
        self.remember.default = config_value('DEFAULT_REMEMBER_ME')
        if current_app.extensions['security'].recoverable and \
                not self.password.description:
            html = Markup(u'<a href="{url}">{message}</a>'.format(
                url=url_for_security("forgot_password"),
                message=get_message("FORGOT_PASSWORD")[0],
            ))
            self.password.description = html

    def validate(self):
        if not super(LoginForm, self).validate():
            return False

        self.user = _datastore.get_user(self.email.data)

        if self.user is None:
            self.email.errors.append(get_message('USER_DOES_NOT_EXIST')[0])
            # Reduce timing variation between existing and non-existung users
            hash_password(self.password.data)
            return False
        if not self.user.password:
            self.password.errors.append(get_message('PASSWORD_NOT_SET')[0])
            # Reduce timing variation between existing and non-existung users
            hash_password(self.password.data)
            return False
        if not self.user.verify_and_update_password(self.password.data):
            self.password.errors.append(get_message('INVALID_PASSWORD')[0])
            return False
        if requires_confirmation(self.user):
            self.email.errors.append(get_message('CONFIRMATION_REQUIRED')[0])
            return False
        if not self.user.is_active:
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False
        return True


class ConfirmRegisterForm(Form, RegisterFormMixin,
                          UniqueEmailFormMixin, NewPasswordFormMixin):
    pass


class RegisterForm(ConfirmRegisterForm, PasswordConfirmFormMixin,
                   NextFormMixin):
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        if not self.next.data:
            self.next.data = request.args.get('next', '')


class ResetPasswordForm(Form, NewPasswordFormMixin, PasswordConfirmFormMixin):
    """The default reset password form"""

    submit = SubmitField(get_form_field_label('reset_password'))


class ChangePasswordForm(Form, PasswordFormMixin):
    """The default change password form"""

    new_password = PasswordField(
        get_form_field_label('new_password'),
        validators=[password_required, password_length])

    new_password_confirm = PasswordField(
        get_form_field_label('retype_password'),
        validators=[EqualTo('new_password',
                            message='RETYPE_PASSWORD_MISMATCH'),
                    password_required])

    submit = SubmitField(get_form_field_label('change_password'))

    def validate(self):
        if not super(ChangePasswordForm, self).validate():
            return False

        if not current_user.verify_and_update_password(self.password.data):
            self.password.errors.append(get_message('INVALID_PASSWORD')[0])
            return False
        if self.password.data == self.new_password.data:
            self.password.errors.append(get_message('PASSWORD_IS_THE_SAME')[0])
            return False
        return True

# -*- coding: utf-8 -*-
"""
    flask_security.views
    ~~~~~~~~~~~~~~~~~~~~

    Flask-Security views module

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from flask import Blueprint, after_this_request, current_app, jsonify, \
    redirect, request
from flask_login import current_user
from werkzeug.datastructures import MultiDict
from werkzeug.local import LocalProxy

from .changeable import change_user_password
from .confirmable import confirm_email_token_status, confirm_user, \
    send_confirmation_instructions
from .decorators import anonymous_user_required, login_required
from .passwordless import login_token_status, send_login_instructions
from .recoverable import reset_password_token_status, \
    send_reset_password_instructions, update_password
from .registerable import register_user
from .utils import url_for_security as url_for
from .utils import config_value, do_flash, get_message, \
    get_post_login_redirect, get_post_logout_redirect, \
    get_post_register_redirect, get_url, login_user, logout_user, \
    slash_url_suffix

# Convenient references
_security = LocalProxy(lambda: current_app.extensions['security'])

_datastore = LocalProxy(lambda: _security.datastore)


def _render_json(form, include_user=True, include_auth_token=False):
    has_errors = len(form.errors) > 0

    if has_errors:
        code = 400
        response = dict(errors=form.errors)
    else:
        code = 200
        response = dict()
        if include_user:
            response['user'] = form.user.get_security_payload()

        if include_auth_token:
            token = form.user.get_auth_token()
            response['user']['authentication_token'] = token

    return jsonify(dict(meta=dict(code=code), response=response)), code


def _commit(response=None):
    _datastore.commit()
    return response


def _ctx(endpoint):
    return _security._run_ctx_processor(endpoint)


@anonymous_user_required
def login():
    """View function for login view"""

    form_class = _security.login_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class(request.form)

    if form.validate_on_submit():
        login_user(form.user, remember=form.remember.data)
        after_this_request(_commit)

        if not request.is_json:
            return redirect(get_post_login_redirect(form.next.data))

    if request.is_json:
        return _render_json(form, include_auth_token=True)

    return _security.render_template(config_value('LOGIN_USER_TEMPLATE'),
                                     login_user_form=form,
                                     **_ctx('login'))


def logout():
    """View function which handles a logout request."""

    if current_user.is_authenticated:
        logout_user()

    return redirect(get_post_logout_redirect())


@anonymous_user_required
def register():
    """View function which handles a registration request."""

    if _security.confirmable or request.is_json:
        form_class = _security.confirm_register_form
    else:
        form_class = _security.register_form

    if request.is_json:
        form_data = MultiDict(request.get_json())
    else:
        form_data = request.form

    form = form_class(form_data)

    if form.validate_on_submit():
        user = register_user(**form.to_dict())
        form.user = user

        if not _security.confirmable or _security.login_without_confirmation:
            after_this_request(_commit)
            login_user(user)

        if not request.is_json:
            if 'next' in form:
                redirect_url = get_post_register_redirect(form.next.data)
            else:
                redirect_url = get_post_register_redirect()

            return redirect(redirect_url)
        return _render_json(form, include_auth_token=True)

    if request.is_json:
        return _render_json(form)

    return _security.render_template(config_value('REGISTER_USER_TEMPLATE'),
                                     register_user_form=form,
                                     **_ctx('register'))


def send_login():
    """View function that sends login instructions for passwordless login"""

    form_class = _security.passwordless_login_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class()

    if form.validate_on_submit():
        send_login_instructions(form.user)
        if not request.is_json:
            do_flash(*get_message('LOGIN_EMAIL_SENT', email=form.user.email))

    if request.is_json:
        return _render_json(form)

    return _security.render_template(config_value('SEND_LOGIN_TEMPLATE'),
                                     send_login_form=form,
                                     **_ctx('send_login'))


@anonymous_user_required
def token_login(token):
    """View function that handles passwordless login via a token"""

    expired, invalid, user = login_token_status(token)

    if invalid:
        do_flash(*get_message('INVALID_LOGIN_TOKEN'))
    if expired:
        send_login_instructions(user)
        do_flash(*get_message('LOGIN_EXPIRED', email=user.email,
                              within=_security.login_within))
    if invalid or expired:
        return redirect(url_for('login'))

    login_user(user)
    after_this_request(_commit)
    do_flash(*get_message('PASSWORDLESS_LOGIN_SUCCESSFUL'))

    return redirect(get_post_login_redirect())


def send_confirmation():
    """View function which sends confirmation instructions."""

    form_class = _security.send_confirmation_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class()

    if form.validate_on_submit():
        send_confirmation_instructions(form.user)
        if not request.is_json:
            do_flash(*get_message('CONFIRMATION_REQUEST',
                     email=form.user.email))

    if request.is_json:
        return _render_json(form)

    return _security.render_template(
        config_value('SEND_CONFIRMATION_TEMPLATE'),
        send_confirmation_form=form,
        **_ctx('send_confirmation')
    )


def confirm_email(token):
    """View function which handles a email confirmation request."""

    expired, invalid, user = confirm_email_token_status(token)

    if not user or invalid:
        invalid = True
        do_flash(*get_message('INVALID_CONFIRMATION_TOKEN'))

    already_confirmed = user is not None and user.confirmed_at is not None

    if expired and not already_confirmed:
        send_confirmation_instructions(user)
        do_flash(*get_message('CONFIRMATION_EXPIRED', email=user.email,
                              within=_security.confirm_email_within))
    if invalid or (expired and not already_confirmed):
        return redirect(get_url(_security.confirm_error_view) or
                        url_for('send_confirmation'))

    if user != current_user:
        logout_user()

    if confirm_user(user):
        after_this_request(_commit)
        msg = 'EMAIL_CONFIRMED'
    else:
        msg = 'ALREADY_CONFIRMED'

    do_flash(*get_message(msg))

    return redirect(get_url(_security.post_confirm_view) or
                    get_url(_security.login_url))


@anonymous_user_required
def forgot_password():
    """View function that handles a forgotten password request."""

    form_class = _security.forgot_password_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class()

    if form.validate_on_submit():
        send_reset_password_instructions(form.user)
        if not request.is_json:
            do_flash(*get_message('PASSWORD_RESET_REQUEST',
                     email=form.user.email))

    if request.is_json:
        return _render_json(form, include_user=False)

    return _security.render_template(config_value('FORGOT_PASSWORD_TEMPLATE'),
                                     forgot_password_form=form,
                                     **_ctx('forgot_password'))


@anonymous_user_required
def reset_password(token):
    """View function that handles a reset password request."""

    expired, invalid, user = reset_password_token_status(token)

    if not user or invalid:
        invalid = True
        do_flash(*get_message('INVALID_RESET_PASSWORD_TOKEN'))

    if expired:
        send_reset_password_instructions(user)
        do_flash(*get_message('PASSWORD_RESET_EXPIRED', email=user.email,
                              within=_security.reset_password_within))
    if invalid or expired:
        return redirect(url_for('forgot_password'))

    form = _security.reset_password_form()

    if form.validate_on_submit():
        after_this_request(_commit)
        update_password(user, form.password.data)
        do_flash(*get_message('PASSWORD_RESET'))
        return redirect(get_url(_security.post_reset_view) or
                        get_url(_security.login_url))

    return _security.render_template(
        config_value('RESET_PASSWORD_TEMPLATE'),
        reset_password_form=form,
        reset_password_token=token,
        **_ctx('reset_password')
    )


@login_required
def change_password():
    """View function which handles a change password request."""

    form_class = _security.change_password_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class()

    if form.validate_on_submit():
        after_this_request(_commit)
        change_user_password(current_user._get_current_object(),
                             form.new_password.data)
        if not request.is_json:
            do_flash(*get_message('PASSWORD_CHANGE'))
            return redirect(get_url(_security.post_change_view) or
                            get_url(_security.post_login_view))

    if request.is_json:
        form.user = current_user
        return _render_json(form)

    return _security.render_template(
        config_value('CHANGE_PASSWORD_TEMPLATE'),
        change_password_form=form,
        **_ctx('change_password')
    )


def create_blueprint(state, import_name):
    """Creates the security extension blueprint"""

    bp = Blueprint(state.blueprint_name, import_name,
                   url_prefix=state.url_prefix,
                   subdomain=state.subdomain,
                   template_folder='templates')

    if state.logoutable:
        bp.route(state.logout_url, endpoint='logout')(logout)

    if state.passwordless:
        bp.route(state.login_url,
                 methods=['GET', 'POST'],
                 endpoint='login')(send_login)
        bp.route(state.login_url + slash_url_suffix(state.login_url,
                                                    '<token>'),
                 endpoint='token_login')(token_login)
    elif state.loginable:
        bp.route(state.login_url,
                 methods=['GET', 'POST'],
                 endpoint='login')(login)

    if state.registerable:
        bp.route(state.register_url,
                 methods=['GET', 'POST'],
                 endpoint='register')(register)

    if state.recoverable:
        bp.route(state.reset_url,
                 methods=['GET', 'POST'],
                 endpoint='forgot_password')(forgot_password)
        bp.route(state.reset_url + slash_url_suffix(state.reset_url,
                                                    '<token>'),
                 methods=['GET', 'POST'],
                 endpoint='reset_password')(reset_password)

    if state.changeable:
        bp.route(state.change_url,
                 methods=['GET', 'POST'],
                 endpoint='change_password')(change_password)

    if state.confirmable:
        bp.route(state.confirm_url,
                 methods=['GET', 'POST'],
                 endpoint='send_confirmation')(send_confirmation)
        bp.route(state.confirm_url + slash_url_suffix(state.confirm_url,
                                                      '<token>'),
                 methods=['GET', 'POST'],
                 endpoint='confirm_email')(confirm_email)

    return bp

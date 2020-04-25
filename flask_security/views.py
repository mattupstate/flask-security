# -*- coding: utf-8 -*-
"""
    flask_security.views
    ~~~~~~~~~~~~~~~~~~~~

    Flask-Security views module

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from flask import current_app, redirect, request, jsonify, \
    after_this_request, Blueprint, session, abort
from flask_login import current_user
from werkzeug.datastructures import MultiDict
from werkzeug.local import LocalProxy
import pyqrcode

from .changeable import change_user_password
from .confirmable import confirm_email_token_status, confirm_user, \
    send_confirmation_instructions
from .decorators import anonymous_user_required, login_required
from .passwordless import login_token_status, send_login_instructions
from .recoverable import reset_password_token_status, \
    send_reset_password_instructions, update_password
from .registerable import register_user
from .utils import config_value, do_flash, get_url, get_post_login_redirect, \
    get_post_register_redirect, get_message, login_user, logout_user, \
    url_for_security as url_for, slash_url_suffix, send_mail,\
    get_post_logout_redirect
from .twofactor import send_security_token, generate_totp, \
    complete_two_factor_process, get_totp_uri

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
    if config_value('TWO_FACTOR') is True and 'password_confirmed' in session:
        del session['password_confirmed']

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


@anonymous_user_required
def two_factor_login():
    """View function for two-factor authentication login"""
    # if we already validated email&password, there is no need to do it again
    form_class = _security.login_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class()

    # if user's email&password approved
    if form.validate_on_submit():
        user = form.user
        session['email'] = user.email
        # if user's two-factor properties are not configured

        if user.two_factor_primary_method is None or\
                user.totp_secret is None:
            session['has_two_factor'] = False
            if not request.is_json:
                return redirect(url_for('two_factor_setup_function'))

        # if user's two-factor properties are configured
        else:
            session['has_two_factor'] = True
            session['primary_method'] = user.two_factor_primary_method
            session['totp_secret'] = user.totp_secret
            send_security_token(user=user,
                                method=user.two_factor_primary_method,
                                totp_secret=user.totp_secret)
            if not request.is_json:
                return redirect(url_for('two_factor_token_validation'))

    if request.is_json:
        return _render_json(form, include_user=False)

    return _security.render_template(config_value('LOGIN_USER_TEMPLATE'),
                                     login_user_form=form,
                                     **_ctx('login'))


def two_factor_setup_function():
    """View function for two-factor setup during login process"""

    # user's email&password not approved or we are
    # logged in and didn't validate password
    form_class = _security.two_factor_setup_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class()

    if 'password_confirmed' not in session:

        if 'email' not in session or 'has_two_factor' not in session:
            if not request.is_json:
                do_flash(*get_message('TWO_FACTOR_PERMISSION_DENIED'))
                return redirect(get_url(_security.login_url))
            else:
                m, c = get_message('TWO_FACTOR_PERMISSION_DENIED')
                form._errors = m
                return _render_json(form)

        # user's email&password approved and
        # two-factor properties were configured before
        if session['has_two_factor'] is True:
            if not request.is_json:
                do_flash(*get_message('TWO_FACTOR_PERMISSION_DENIED'))
                return redirect(url_for('two_factor_token_validation'))
            else:
                m, c = get_message('TWO_FACTOR_PERMISSION_DENIED')
                form._errors = m
                return _render_json(form)

        user = _datastore.find_user(email=session['email'])
    else:
        user = current_user

    if form.validate_on_submit():
        # totp and primary_method are added to
        # session to flag the user's temporary choice
        session['totp_secret'] = generate_totp()
        session['primary_method'] = form['setup'].data
        if len(form.data['phone']) > 0:
            session['phone_number'] = form.data['phone']
        send_security_token(user=user, method=session['primary_method'],
                            totp_secret=session['totp_secret'])
        code_form = _security.two_factor_verify_code_form()
        if not request.is_json:
            return _security.render_template(
                config_value('TWO_FACTOR_CHOOSE_METHOD_TEMPLATE'),
                two_factor_setup_form=form,
                two_factor_verify_code_form=code_form,
                choices=config_value(
                    'TWO_FACTOR_ENABLED_METHODS'),
                chosen_method=session['primary_method'],
                **_ctx('two_factor_setup_function'))

    if request.is_json:
        return _render_json(form, include_user=False)

    code_form = _security.two_factor_verify_code_form()
    return _security.render_template(
        config_value('TWO_FACTOR_CHOOSE_METHOD_TEMPLATE'),
        two_factor_setup_form=form,
        two_factor_verify_code_form=code_form,
        choices=config_value(
            'TWO_FACTOR_ENABLED_METHODS'),
        **_ctx('two_factor_setup_function'))


def two_factor_token_validation():
    """View function for two-factor token validation during login process"""
    # if we are in login process and not changing current two-factor method

    form_class = _security.two_factor_verify_code_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class()

    if 'password_confirmed' not in session:
        # user's email&password not approved or we are logged in
        # and didn't validate password
        if 'has_two_factor' not in session:
            if not request.is_json:
                do_flash(*get_message('TWO_FACTOR_PERMISSION_DENIED'))
                return redirect(get_url(_security.login_url))
            else:
                m, c = get_message('TWO_FACTOR_PERMISSION_DENIED')
                form._errors = m
                return _render_json(form)
        # make sure user has or has chosen a two-factor
        # method before we try to validate
        if 'totp_secret' not in session or 'primary_method' not in session:
            if not request.is_json:
                do_flash(*get_message('TWO_FACTOR_PERMISSION_DENIED'))
                return redirect(url_for('two_factor_setup_function'))
            else:
                m, c = get_message('TWO_FACTOR_PERMISSION_DENIED')
                form._errors = m
                return _render_json(form)

    if form.validate_on_submit():
        complete_two_factor_process(form.user)
        after_this_request(_commit)
        if not request.is_json:
            return redirect(get_post_login_redirect())

    if request.is_json:
        form.user = current_user
        return _render_json(form)

    # if we were trying to validate a new method
    if 'password_confirmed' in session or session['has_two_factor'] is False:
        setup_form = _security.two_factor_setup_form()

        return _security.render_template(
            config_value('TWO_FACTOR_CHOOSE_METHOD_TEMPLATE'),
            two_factor_setup_form=setup_form,
            two_factor_verify_code_form=form,
            choices=config_value(
                'TWO_FACTOR_ENABLED_METHODS'),
            **_ctx('two_factor_setup_function'))

    # if we were trying to validate an existing method
    else:

        rescue_form = _security.two_factor_rescue_form()

        return _security.render_template(
            config_value('TWO_FACTOR_VERIFY_CODE_TEMPLATE'),
            two_factor_rescue_form=rescue_form,
            two_factor_verify_code_form=form,
            problem=None,
            **_ctx('two_factor_token_validaion'))


@anonymous_user_required
def two_factor_rescue_function():
    """ Function that handles a situation where user can't
    enter his two-factor validation code"""
    # user's email&password yet to be approved

    form_class = _security.two_factor_rescue_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class()

    if 'email' not in session:
        if not request.is_json:
            do_flash(*get_message('TWO_FACTOR_PERMISSION_DENIED'))
            return redirect(get_url(_security.login_url))
        else:
            m, c = get_message('TWO_FACTOR_PERMISSION_DENIED')
            form._errors = m
            return _render_json(form, include_user=False)
    # user's email&password approved and two-factor properties
    # were not configured
    if 'totp_secret' not in session or 'primary_method' not in session:
        if not request.is_json:
            do_flash(*get_message('TWO_FACTOR_PERMISSION_DENIED'))
            return redirect(get_url(_security.login_url))

        else:
            m, c = get_message('TWO_FACTOR_PERMISSION_DENIED')
            form._errors = m
            return _render_json(form, include_user=False)

    problem = None
    if form.validate_on_submit():
        problem = form.data['help_setup']
        # if the problem is that user can't access his device, w
        # e send him code through mail
        if problem == 'lost_device':
            send_security_token(user=form.user, method='mail',
                                totp_secret=form.user.totp_secret)
        # send app provider a mail message regarding trouble
        elif problem == 'no_mail_access':
            send_mail(config_value('EMAIL_SUBJECT_TWO_FACTOR_RESCUE'),
                      config_value('TWO_FACTOR_RESCUE_MAIL'),
                      'two_factor_rescue',
                      user=form.user)
        else:
            return "", 404

    if request.is_json:
        return _render_json(form, include_user=False)

    code_form = _security.two_factor_verify_code_form()
    return _security.render_template(
        config_value('TWO_FACTOR_VERIFY_CODE_TEMPLATE'),
        two_factor_verify_code_form=code_form,
        two_factor_rescue_form=form,
        rescue_mail=config_value(
            'TWO_FACTOR_RESCUE_MAIL'),
        problem=str(problem),
        **_ctx('two_factor_token_validation'))


@login_required
def two_factor_password_confirmation():
    """View function which handles a change two-factor method request."""
    form_class = _security.two_factor_change_method_verify_password_form

    if request.is_json:
        form = form_class(MultiDict(request.get_json()))
    else:
        form = form_class()

    if form.validate_on_submit():
        session['password_confirmed'] = True
        if not request.is_json:
            do_flash(get_message('TWO_FACTOR_PASSWORD_CONFIRMATION_DONE'))
            return redirect(url_for('two_factor_setup_function'))

        else:
            m, c = get_message('TWO_FACTOR_PASSWORD_CONFIRMATION_DONE')
            form._errors = m
            return _render_json(form)

    if request.is_json:
        form.user = current_user
        return _render_json(form)

    return _security.render_template(
        config_value(
            'TWO_FACTOR_CHANGE_METHOD_PASSWORD_CONFIRMATION_TEMPLATE'),
        two_factor_change_method_verify_password_form=form,
        **_ctx('two_factor_change_method_password_confirmation'))


def two_factor_qrcode():
    return generate_qrcode()


def generate_qrcode():
    if 'google_authenticator' not in\
            config_value('TWO_FACTOR_ENABLED_METHODS'):
        return abort(404)
    if 'primary_method' not in session or\
        session['primary_method'] != 'google_authenticator' \
            or 'totp_secret' not in session:
        return abort(404)

    if 'email' in session:
        email = session['email']
    elif 'password_confirmed' in session:
        email = current_user.email
    else:
        return abort(404)

    name = email.split('@')[0]
    totp = session['totp_secret']
    url = pyqrcode.create(get_totp_uri(name, totp))
    from io import BytesIO
    stream = BytesIO()
    url.svg(stream, scale=3)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}


def create_blueprint(state, import_name):
    """Creates the security extension blueprint"""

    bp = Blueprint(state.blueprint_name, import_name,
                   url_prefix=state.url_prefix,
                   subdomain=state.subdomain,
                   template_folder='templates')

    bp.route(state.logout_url, endpoint='logout')(logout)

    if state.passwordless:
        bp.route(state.login_url,
                 methods=['GET', 'POST'],
                 endpoint='login')(send_login)
        bp.route(state.login_url + slash_url_suffix(state.login_url,
                                                    '<token>'),
                 endpoint='token_login')(token_login)

    elif state.two_factor:
        tf_setup_function = 'two_factor_setup_function'
        tf_token_validation = 'two_factor_token_validation'
        tf_qrcode = 'two_factor_qrcode'
        tf_rescue_function = 'two_factor_rescue_function'
        tf_pass_validation = 'two_factor_password_confirmation'
        bp.route(state.login_url,
                 methods=['GET', 'POST'],
                 endpoint='login')(two_factor_login)
        bp.route('/' + slash_url_suffix('/', tf_setup_function),
                 methods=['GET', 'POST'],
                 endpoint=tf_setup_function)(two_factor_setup_function)
        bp.route('/' + slash_url_suffix('/', tf_token_validation),
                 methods=['GET', 'POST'],
                 endpoint=tf_token_validation)(two_factor_token_validation)
        bp.route('/' + slash_url_suffix('/', tf_qrcode),
                 endpoint=tf_qrcode)(two_factor_qrcode)
        bp.route('/' + slash_url_suffix('/', tf_rescue_function),
                 methods=['GET', 'POST'],
                 endpoint=tf_rescue_function)(two_factor_rescue_function)
        bp.route(state.change_url + slash_url_suffix(
            state.change_url, tf_pass_validation),
            methods=['GET', 'POST'],
            endpoint=tf_pass_validation)(two_factor_password_confirmation)

    else:
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

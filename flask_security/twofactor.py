# -*- coding: utf-8 -*-
"""
    flask_security.two_factor
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Flask-Security two_factor module

    :copyright: (c) 2016 by Gal Stainfeld, at Emedgene
"""

import os
import base64
from passlib.totp import TOTP

import onetimepass
from flask import current_app as app, session
from werkzeug.local import LocalProxy

from .utils import send_mail, config_value, get_message, do_flash,\
    SmsSenderFactory, login_user
from .signals import user_two_factored, two_factor_method_changed

# Convenient references
_security = LocalProxy(lambda: app.extensions['security'])

_datastore = LocalProxy(lambda: _security.datastore)


def send_security_token(user, method, totp_secret):
    """Sends the security token via email for the specified user.
    :param user: The user to send the code to
    :param method: The method in which the code will be sent
                ('mail' or 'sms') at the moment
    :param totp_secret: a unique shared secret of the user
    """
    token_to_be_sent = get_totp_password(totp_secret)
    if method == 'mail':
        send_mail(config_value('EMAIL_SUBJECT_TWO_FACTOR'),
                  user.email,
                  'two_factor_instructions',
                  user=user,
                  token=token_to_be_sent)
    elif method == 'sms':
        msg = "Use this code to log in: %s" % token_to_be_sent
        from_number = config_value('TWO_FACTOR_SMS_SERVICE_CONFIG')[
            'PHONE_NUMBER']
        if 'phone_number' in session:
            to_number = session['phone_number']
        else:
            to_number = user.phone_number
        sms_sender = SmsSenderFactory.createSender(
            config_value('TWO_FACTOR_SMS_SERVICE'))
        sms_sender.send_sms(from_number=from_number,
                            to_number=to_number, msg=msg)

    elif method == 'google_authenticator':
        # password are generated automatically in the google authenticator app
        pass


def get_totp_uri(username, totp_secret):
    """ Generate provisioning url for use with the qrcode
            scanner built into the app
    :param username: username of the current user
    :param totp_secret: a unique shared secret of the user
    :return:
    """
    tp = TOTP(totp_secret)
    service_name = config_value('TWO_FACTOR_URI_SERVICE_NAME')
    return tp.to_uri(username + '@' + service_name, service_name)


def verify_totp(token, totp_secret, window=0):
    """ Verifies token for specific user_totp
    :param token - token to be check against user's secret
    :param totp_secret - a unique shared secret of the user
    :param window - optional, compensate for clock skew, number of
        intervals to check on each side of the current time.
        (default is 0 - only check the current clock time)
    :return:
    """
    return onetimepass.valid_totp(token, totp_secret, window=window)


def get_totp_password(totp_secret):
    """Get time-based one-time password on the basis of given secret and time
    :param totp_secret - a unique shared secret of the user
    """
    return onetimepass.get_totp(totp_secret)


def generate_totp():
    return base64.b32encode(os.urandom(10)).decode('utf-8')


def complete_two_factor_process(user):
    """clean session according to process (login or changing two-factor method)
     and perform action accordingly
    :param user - user's to update in database and log in if necessary
    """
    totp_secret_changed = user.totp_secret != session['totp_secret']
    if totp_secret_changed or user.two_factor_primary_method\
            != session['primary_method']:
        user.totp_secret = session['totp_secret']
        user.two_factor_primary_method = session['primary_method']

        if 'phone_number' in session:
            user.phone_number = session['phone_number']
            del session['phone_number']

        _datastore.put(user)

    del session['primary_method']
    del session['totp_secret']

    # if we are changing two-factor method
    if 'password_confirmed' in session:
        del session['password_confirmed']
        do_flash(*get_message('TWO_FACTOR_CHANGE_METHOD_SUCCESSFUL'))
        two_factor_method_changed.send(app._get_current_object(),
                                       user=user)

    # if we are logging in for the first time
    else:
        del session['email']
        del session['has_two_factor']
        do_flash(*get_message('TWO_FACTOR_LOGIN_SUCCESSFUL'))
        user_two_factored.send(app._get_current_object(), user=user)
        login_user(user)
    return

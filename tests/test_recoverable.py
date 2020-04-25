# -*- coding: utf-8 -*-
"""
    test_recoverable
    ~~~~~~~~~~~~~~~~

    Recoverable functionality tests
"""

import time

import pytest
from flask import Flask
from utils import authenticate, logout

from flask_security.core import UserMixin
from flask_security.forms import LoginForm
from flask_security.signals import password_reset, \
    reset_password_instructions_sent
from flask_security.utils import capture_reset_password_requests, string_types

pytestmark = pytest.mark.recoverable()


def test_recoverable_flag(app, client, get_message):
    recorded_resets = []
    recorded_instructions_sent = []

    @password_reset.connect_via(app)
    def on_password_reset(app, user):
        recorded_resets.append(user)

    @reset_password_instructions_sent.connect_via(app)
    def on_instructions_sent(app, user, token):
        assert isinstance(app, Flask)
        assert isinstance(user, UserMixin)
        assert isinstance(token, string_types)
        recorded_instructions_sent.append(user)

    # Test the reset view
    response = client.get('/reset')
    assert b'<h1>Send password reset instructions</h1>' in response.data

    # Test submitting email to reset password creates a token and sends email
    with capture_reset_password_requests() as requests:
        with app.mail.record_messages() as outbox:
            response = client.post(
                '/reset',
                data=dict(
                    email='joe@lp.com'),
                follow_redirects=True)

    assert len(recorded_instructions_sent) == 1
    assert len(outbox) == 1
    assert response.status_code == 200
    assert get_message(
        'PASSWORD_RESET_REQUEST',
        email='joe@lp.com') in response.data
    token = requests[0]['token']

    # Test view for reset token
    response = client.get('/reset/' + token)
    assert b'<h1>Reset password</h1>' in response.data

    # Test submitting a new password
    response = client.post('/reset/' + token, data={
        'password': 'newpassword',
        'password_confirm': 'newpassword'
    }, follow_redirects=True)

    assert get_message('PASSWORD_RESET') in response.data
    assert len(recorded_resets) == 1
    assert b'Hello joe@lp.com' not in response.data

    logout(client)

    # Test logging in with the new password
    response = authenticate(
        client,
        'joe@lp.com',
        'newpassword',
        follow_redirects=True)
    assert b'Hello joe@lp.com' in response.data

    logout(client)

    # Test submitting JSON
    response = client.post('/reset', data='{"email": "joe@lp.com"}', headers={
        'Content-Type': 'application/json'
    })
    assert response.headers['Content-Type'] == 'application/json'
    assert 'user' not in response.jdata['response']

    logout(client)

    # Test invalid email
    response = client.post(
        '/reset',
        data=dict(
            email='bogus@lp.com'),
        follow_redirects=True)
    assert get_message('USER_DOES_NOT_EXIST') in response.data

    logout(client)

    # Test invalid token
    response = client.post('/reset/bogus', data={
        'password': 'newpassword',
        'password_confirm': 'newpassword'
    }, follow_redirects=True)
    assert get_message('INVALID_RESET_PASSWORD_TOKEN') in response.data

    # Test mangled token
    token = (
        "WyIxNjQ2MzYiLCIxMzQ1YzBlZmVhM2VhZjYwODgwMDhhZGU2YzU0MzZjMiJd."
        "BZEw_Q.lQyo3npdPZtcJ_sNHVHP103syjM"
        "&url_id=fbb89a8328e58c181ea7d064c2987874bc54a23d")
    response = client.post('/reset/' + token, data={
        'password': 'newpassword',
        'password_confirm': 'newpassword'
    }, follow_redirects=True)
    assert get_message('INVALID_RESET_PASSWORD_TOKEN') in response.data


def test_login_form_description(sqlalchemy_app):
    app = sqlalchemy_app()
    with app.test_request_context('/login'):
        login_form = LoginForm()
        expected = '<a href="/reset">Forgot password?</a>'
        assert login_form.password.description == expected


@pytest.mark.settings(reset_password_within='1 milliseconds')
def test_expired_reset_token(client, get_message):
    with capture_reset_password_requests() as requests:
        client.post(
            '/reset',
            data=dict(
                email='joe@lp.com'),
            follow_redirects=True)

    user = requests[0]['user']
    token = requests[0]['token']

    time.sleep(1)

    response = client.post('/reset/' + token, data={
        'password': 'newpassword',
        'password_confirm': 'newpassword'
    }, follow_redirects=True)

    msg = get_message(
        'PASSWORD_RESET_EXPIRED',
        within='1 milliseconds',
        email=user.email)
    assert msg in response.data


def test_reset_token_deleted_user(app, client, get_message,
                                  sqlalchemy_datastore):
    with capture_reset_password_requests() as requests:

        client.post(
            '/reset',
            data=dict(
                email='gene@lp.com'),
            follow_redirects=True)

    user = requests[0]['user']
    token = requests[0]['token']

    # Delete user
    with app.app_context():
        sqlalchemy_datastore.delete(user)
        sqlalchemy_datastore.commit()

    response = client.post('/reset/' + token, data={
        'password': 'newpassword',
        'password_confirm': 'newpassword'
    }, follow_redirects=True)

    msg = get_message('INVALID_RESET_PASSWORD_TOKEN')
    assert msg in response.data


def test_used_reset_token(client, get_message):
    with capture_reset_password_requests() as requests:
        client.post(
            '/reset',
            data=dict(
                email='joe@lp.com'),
            follow_redirects=True)

    token = requests[0]['token']

    # use the token
    response = client.post('/reset/' + token, data={
        'password': 'newpassword',
        'password_confirm': 'newpassword'
    }, follow_redirects=True)

    assert get_message('PASSWORD_RESET') in response.data

    logout(client)

    # attempt to use it a second time
    response2 = client.post('/reset/' + token, data={
        'password': 'otherpassword',
        'password_confirm': 'otherpassword'
    }, follow_redirects=True)

    msg = get_message('INVALID_RESET_PASSWORD_TOKEN')
    assert msg in response2.data


def test_reset_token_redirect(client, get_message):
    with capture_reset_password_requests() as requests:
        client.post(
            '/reset',
            data=dict(
                email='joe@lp.com'),
            follow_redirects=True)

    token = requests[0]['token']

    response = client.post('/reset/' + token, data={
        'password': 'newpassword',
        'password_confirm': 'newpassword'
    })

    assert 'location' in response.headers
    assert '/login' in response.location

    response = client.get(response.location)
    assert get_message('PASSWORD_RESET') in response.data


@pytest.mark.settings(post_reset_view='/post_reset')
def test_reset_token_redirect_to_post_reset(client, get_message):
    with capture_reset_password_requests() as requests:
        client.post(
            '/reset',
            data=dict(
                email='joe@lp.com'),
            follow_redirects=True)

    token = requests[0]['token']

    response = client.post('/reset/' + token, data={
        'password': 'newpassword',
        'password_confirm': 'newpassword'
    }, follow_redirects=True)
    assert b'Post Reset' in response.data


def test_reset_passwordless_user(client, get_message):
    with capture_reset_password_requests() as requests:
        client.post(
            '/reset',
            data=dict(
                email='jess@lp.com'),
            follow_redirects=True)

    token = requests[0]['token']

    # use the token
    response = client.post('/reset/' + token, data={
        'password': 'newpassword',
        'password_confirm': 'newpassword'
    }, follow_redirects=True)

    assert get_message('PASSWORD_RESET') in response.data


@pytest.mark.settings(reset_url='/custom_reset')
def test_custom_reset_url(client):
    response = client.get('/custom_reset')
    assert response.status_code == 200


@pytest.mark.settings(
    reset_password_template='custom_security/reset_password.html',
    forgot_password_template='custom_security/forgot_password.html')
def test_custom_reset_templates(client):
    response = client.get('/reset')
    assert b'CUSTOM FORGOT PASSWORD' in response.data

    with capture_reset_password_requests() as requests:
        client.post(
            '/reset',
            data=dict(
                email='joe@lp.com'),
            follow_redirects=True)
        token = requests[0]['token']

    response = client.get('/reset/' + token)
    assert b'CUSTOM RESET PASSWORD' in response.data

# -*- coding: utf-8 -*-
"""
    test_common
    ~~~~~~~~~~~

    Test common functionality
"""

import base64

import pytest

from utils import authenticate, json_authenticate, logout

try:
    from cookielib import Cookie
except ImportError:
    from http.cookiejar import Cookie


def test_login_view(client):
    response = client.get('/login')
    assert b'<h1>Login</h1>' in response.data


def test_authenticate(client):
    response = authenticate(client)
    assert response.status_code == 302
    response = authenticate(client, follow_redirects=True)
    assert b'Hello matt@lp.com' in response.data


def test_authenticate_with_next(client):
    data = dict(email='matt@lp.com', password='password')
    response = client.post(
        '/login?next=/page1',
        data=data,
        follow_redirects=True)
    assert b'Page 1' in response.data


def test_authenticate_with_invalid_next(client, get_message):
    data = dict(email='matt@lp.com', password='password')
    response = client.post('/login?next=http://google.com', data=data)
    assert get_message('INVALID_REDIRECT') in response.data


def test_authenticate_with_invalid_malformed_next(client, get_message):
    data = dict(email='matt@lp.com', password='password')
    response = client.post('/login?next=http:///google.com', data=data)
    assert get_message('INVALID_REDIRECT') in response.data


def test_authenticate_case_insensitive_email(app, client):
    response = authenticate(client, 'MATT@lp.com', follow_redirects=True)
    assert b'Hello matt@lp.com' in response.data


def test_authenticate_with_invalid_input(client, get_message):
    response = client.post(
        '/login',
        data='{}',
        headers={'Content-Type': 'application/json'},
    )
    assert get_message('EMAIL_NOT_PROVIDED') in response.data


def test_login_form(client):
    response = client.post('/login', data={'email': 'matt@lp.com'})
    assert b'matt@lp.com' in response.data


def test_unprovided_username(client, get_message):
    response = authenticate(client, "")
    assert get_message('EMAIL_NOT_PROVIDED') in response.data


def test_unprovided_password(client, get_message):
    response = authenticate(client, password="")
    assert get_message('PASSWORD_NOT_PROVIDED') in response.data


def test_invalid_user(client, get_message):
    response = authenticate(client, email="bogus@bogus.com")
    assert get_message('USER_DOES_NOT_EXIST') in response.data


def test_bad_password(client, get_message):
    response = authenticate(client, password="bogus")
    assert get_message('INVALID_PASSWORD') in response.data


def test_inactive_user(client, get_message):
    response = authenticate(client, "tiya@lp.com", "password")
    assert get_message('DISABLED_ACCOUNT') in response.data


def test_unset_password(client, get_message):
    response = authenticate(client, "jess@lp.com", "password")
    assert get_message('PASSWORD_NOT_SET') in response.data


def test_logout(client):
    authenticate(client)
    response = logout(client, follow_redirects=True)
    assert b'Home Page' in response.data


def test_logout_with_next(client, get_message):
    authenticate(client)
    response = client.get('/logout?next=http://google.com')
    assert 'google.com' not in response.location


def test_missing_session_access(client, get_message):
    response = client.get('/profile', follow_redirects=True)
    assert get_message('LOGIN') in response.data


def test_has_session_access(client):
    authenticate(client)
    response = client.get("/profile", follow_redirects=True)
    assert b'profile' in response.data


def test_authorized_access(client):
    authenticate(client)
    response = client.get("/admin")
    assert b'Admin Page' in response.data


def test_unauthorized_access(client, get_message):
    authenticate(client, "joe@lp.com")
    response = client.get("/admin", follow_redirects=True)
    assert response.status_code == 403


@pytest.mark.settings(unauthorized_view=lambda: None)
def test_unauthorized_access_with_referrer(client, get_message):
    authenticate(client, 'joe@lp.com')
    response = client.get('/admin', headers={'referer': '/admin'})
    assert response.headers['Location'] != '/admin'
    client.get(response.headers['Location'])

    response = client.get(
        '/admin?a=b',
        headers={'referer': 'http://localhost/admin?x=y'}
    )
    assert response.headers['Location'] == 'http://localhost/'
    client.get(response.headers['Location'])

    response = client.get('/admin',
                          headers={'referer': '/admin'},
                          follow_redirects=True)
    assert response.data.count(get_message('UNAUTHORIZED')) == 1


@pytest.mark.settings(unauthorized_view='/')
def test_roles_accepted(client):
    for user in ("matt@lp.com", "joe@lp.com"):
        authenticate(client, user)
        response = client.get("/admin_or_editor")
        assert b'Admin or Editor Page' in response.data
        logout(client)

    authenticate(client, "jill@lp.com")
    response = client.get("/admin_or_editor", follow_redirects=True)
    assert b'Home Page' in response.data


@pytest.mark.settings(unauthorized_view='/')
def test_unauthenticated_role_required(client, get_message):
    response = client.get('/admin', follow_redirects=True)
    assert get_message('UNAUTHORIZED') in response.data


@pytest.mark.settings(unauthorized_view='/')
def test_multiple_role_required(client):
    for user in ("matt@lp.com", "joe@lp.com"):
        authenticate(client, user)
        response = client.get("/admin_and_editor", follow_redirects=True)
        assert b'Home Page' in response.data
        client.get('/logout')

    authenticate(client, 'dave@lp.com')
    response = client.get("/admin_and_editor", follow_redirects=True)
    assert b'Admin and Editor Page' in response.data


def test_ok_json_auth(client):
    response = json_authenticate(client)
    assert response.jdata['meta']['code'] == 200
    assert 'authentication_token' in response.jdata['response']['user']


def test_invalid_json_auth(client):
    response = json_authenticate(client, password='junk')
    assert b'"code": 400' in response.data


def test_token_auth_via_querystring_valid_token(client):
    response = json_authenticate(client)
    token = response.jdata['response']['user']['authentication_token']
    response = client.get('/token?auth_token=' + token)
    assert b'Token Authentication' in response.data


def test_token_auth_via_header_valid_token(client):
    response = json_authenticate(client)
    token = response.jdata['response']['user']['authentication_token']
    headers = {"Authentication-Token": token}
    response = client.get('/token', headers=headers)
    assert b'Token Authentication' in response.data


def test_token_auth_via_querystring_invalid_token(client):
    response = client.get('/token?auth_token=X')
    assert 401 == response.status_code


def test_token_auth_via_header_invalid_token(client):
    response = client.get('/token', headers={"Authentication-Token": 'X'})
    assert 401 == response.status_code


def test_http_auth(client):
    response = client.get('/http', headers={
        'Authorization': 'Basic %s' % base64.b64encode(
            b"joe@lp.com:password").decode('utf-8')
    })
    assert b'HTTP Authentication' in response.data


def test_http_auth_no_authorization(client):
    response = client.get('/http', headers={})
    assert b'<h1>Unauthorized</h1>' in response.data
    assert 'WWW-Authenticate' in response.headers
    assert 'Basic realm="Login Required"' == response.headers[
        'WWW-Authenticate']


def test_invalid_http_auth_invalid_username(client):
    response = client.get('/http', headers={
        'Authorization': 'Basic %s' % base64.b64encode(
            b"bogus:bogus").decode('utf-8')
    })
    assert b'<h1>Unauthorized</h1>' in response.data
    assert 'WWW-Authenticate' in response.headers
    assert 'Basic realm="Login Required"' == response.headers[
        'WWW-Authenticate']


def test_invalid_http_auth_bad_password(client):
    response = client.get('/http', headers={
        'Authorization': 'Basic %s' % base64.b64encode(
            b"joe@lp.com:bogus").decode('utf-8')
    })
    assert b'<h1>Unauthorized</h1>' in response.data
    assert 'WWW-Authenticate' in response.headers
    assert 'Basic realm="Login Required"' == response.headers[
        'WWW-Authenticate']


def test_custom_http_auth_realm(client):
    response = client.get('/http_custom_realm', headers={
        'Authorization': 'Basic %s' % base64.b64encode(
            b"joe@lp.com:bogus").decode('utf-8')
    })
    assert b'<h1>Unauthorized</h1>' in response.data
    assert 'WWW-Authenticate' in response.headers
    assert 'Basic realm="My Realm"' == response.headers['WWW-Authenticate']


def test_multi_auth_basic(client):
    response = client.get('/multi_auth', headers={
        'Authorization': 'Basic %s' % base64.b64encode(
            b"joe@lp.com:password").decode('utf-8')
    })
    assert b'Basic' in response.data

    response = client.get('/multi_auth')
    assert response.status_code == 401


def test_multi_auth_basic_invalid(client):
    response = client.get('/multi_auth', headers={
        'Authorization': 'Basic %s' % base64.b64encode(
            b"bogus:bogus").decode('utf-8')
    })
    assert b'<h1>Unauthorized</h1>' in response.data
    assert 'WWW-Authenticate' in response.headers
    assert 'Basic realm="Login Required"' == response.headers[
        'WWW-Authenticate']

    response = client.get('/multi_auth')
    print(response.headers)
    assert response.status_code == 401


def test_multi_auth_token(client):
    response = json_authenticate(client)
    token = response.jdata['response']['user']['authentication_token']
    response = client.get('/multi_auth?auth_token=' + token)
    assert b'Token' in response.data


def test_multi_auth_session(client):
    authenticate(client, )
    response = client.get('/multi_auth')
    assert b'Session' in response.data


def test_user_deleted_during_session_reverts_to_anonymous_user(app, client):
    authenticate(client)

    with app.test_request_context('/'):
        user = app.security.datastore.find_user(email='matt@lp.com')
        app.security.datastore.delete_user(user)
        app.security.datastore.commit()

    response = client.get('/')
    assert b'Hello matt@lp.com' not in response.data


def test_remember_token(client):
    response = authenticate(client, follow_redirects=False)
    client.cookie_jar.clear_session_cookies()
    response = client.get('/profile')
    assert b'profile' in response.data


def test_request_loader_does_not_fail_with_invalid_token(client):
    c = Cookie(version=0, name='remember_token', value='None', port=None,
               port_specified=False, domain='www.example.com',
               domain_specified=False, domain_initial_dot=False, path='/',
               path_specified=True, secure=False, expires=None,
               discard=True, comment=None, comment_url=None,
               rest={'HttpOnly': None}, rfc2109=False)

    client.cookie_jar.set_cookie(c)
    response = client.get('/')
    assert b'BadSignature' not in response.data


def test_sending_auth_token_with_json(client):
    response = json_authenticate(client)
    token = response.jdata['response']['user']['authentication_token']
    data = '{"auth_token": "%s"}' % token
    response = client.post(
        '/token',
        data=data,
        headers={
            'Content-Type': 'application/json'})
    assert b'Token Authentication' in response.data

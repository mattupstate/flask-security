# -*- coding: utf-8 -*-
"""
    utils
    ~~~~~

    Test utils
"""

from flask import Response as BaseResponse
from flask import json

from flask_security import Security
from flask_security.utils import hash_password

_missing = object


def authenticate(
        client,
        email="matt@lp.com",
        password="password",
        endpoint=None,
        **kwargs):
    data = dict(email=email, password=password, remember='y')
    return client.post(endpoint or '/login', data=data, **kwargs)


def json_authenticate(
        client,
        email="matt@lp.com",
        password="password",
        endpoint=None):
    data = '{"email": "%s", "password": "%s"}' % (email, password)
    return client.post(
        endpoint or '/login',
        content_type="application/json",
        data=data)


def logout(client, endpoint=None, **kwargs):
    return client.get(endpoint or '/logout', **kwargs)


def create_roles(ds):
    for role in ('admin', 'editor', 'author'):
        ds.create_role(name=role)
    ds.commit()


def create_users(ds, count=None):
    users = [('matt@lp.com', 'matt', 'password', ['admin'], True, None, None),
             ('joe@lp.com', 'joe', 'password', ['editor'], True, None, None),
             ('dave@lp.com', 'dave', 'password', [
              'admin', 'editor'], True, None, None),
             ('jill@lp.com', 'jill', 'password', ['author'], True, None, None),
             ('tiya@lp.com', 'tiya', 'password', [], False, None, None),
             ('jess@lp.com', 'jess', None, [], True, None, None),
             ('gal@lp.com', 'gal', 'password', [
              'admin'], True, 'sms', u'RCTE75AP2GWLZIFR'),
             ('gal2@lp.com', 'gal2', 'password', ['admin'], True,
              'google_authenticator', u'RCTE75AP2GWLZIFR'),
             ('gal3@lp.com', 'gal3', 'password', [
              'admin'], True, 'mail', u'RCTE75AP2GWLZIFR'),
             ('gene@lp.com', 'gene', 'password', [], True, None, None)]
    count = count or len(users)

    for u in users[:count]:
        pw = u[2]
        if pw is not None:
            pw = hash_password(pw)
        roles = [ds.find_or_create_role(rn) for rn in u[3]]
        ds.commit()
        user = ds.create_user(email=u[0],
                              username=u[1],
                              password=pw,
                              active=u[4],
                              two_factor_primary_method=u[5],
                              totp_secret=u[6])
        ds.commit()
        for role in roles:
            ds.add_role_to_user(user, role)
        ds.commit()


def populate_data(app, user_count=None):
    ds = app.security.datastore
    with app.app_context():
        create_roles(ds)
        create_users(ds, user_count)


class Response(BaseResponse):  # pragma: no cover

    @property
    def jdata(self):
        rv = getattr(self, '_cached_jdata', _missing)
        if rv is not _missing:
            return rv
        try:
            self._cached_jdata = json.loads(self.data)
        except ValueError:
            raise Exception('Invalid JSON response')
        return self._cached_jdata


def init_app_with_options(app, datastore, **options):
    security_args = options.pop('security_args', {})
    app.config.update(**options)
    app.security = Security(app, datastore=datastore, **security_args)
    populate_data(app)

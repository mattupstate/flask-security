# -*- coding: utf-8 -*-
"""
    flask.ext.security.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Flask-Security decorators module

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from functools import wraps

from flask import current_app as app, Response, request, abort, redirect
from flask.ext.login import login_required, login_url, current_user
from flask.ext.principal import RoleNeed, Permission

from . import utils


_default_http_auth_msg = """
    <h1>Unauthorized</h1>
    <p>The server could not verify that you are authorized to access the URL
    requested. You either supplied the wrong credentials (e.g. a bad password),
    or your browser doesn't understand how to supply the credentials required.</p>
    <p>In case you are allowed to request the document, please check your
    user-id and password and try again.</p>
    """


def _check_token():
    header_key = app.security.token_authentication_header
    args_key = app.security.token_authentication_key

    header_token = request.headers.get(header_key, None)
    token = request.args.get(args_key, header_token)

    try:
        app.security.datastore.find_user(authentication_token=token)
    except:
        return False

    return True


def _check_http_auth():
    auth = request.authorization or dict(username=None, password=None)

    try:
        user = app.security.datastore.find_user(email=auth.username)
    except:
        return False

    return app.security.pwd_context.verify(auth.password, user.password)


def http_auth_required(fn):
    headers = {'WWW-Authenticate': 'Basic realm="Login Required"'}

    @wraps(fn)
    def decorated(*args, **kwargs):
        if _check_http_auth():
            return fn(*args, **kwargs)

        return Response(_default_http_auth_msg, 401, headers)

    return decorated


def auth_token_required(fn):

    @wraps(fn)
    def decorated(*args, **kwargs):
        if _check_token():
            return fn(*args, **kwargs)

        abort(401)

    return decorated


def roles_required(*roles):
    """View decorator which specifies that a user must have all the specified
    roles. Example::

        @app.route('/dashboard')
        @roles_required('admin', 'editor')
        def dashboard():
            return 'Dashboard'

    The current user must have both the `admin` role and `editor` role in order
    to view the page.

    :param args: The required roles.
    """
    perms = [Permission(RoleNeed(role)) for role in roles]

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated():
                login_view = app.security.login_manager.login_view
                return redirect(login_url(login_view, request.url))

            for perm in perms:
                if not perm.can():
                    app.logger.debug('Identity does not provide the '
                                             'roles: %s' % [r for r in roles])
                    return redirect(request.referrer or '/')
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


def roles_accepted(*roles):
    """View decorator which specifies that a user must have at least one of the
    specified roles. Example::

        @app.route('/create_post')
        @roles_accepted('editor', 'author')
        def create_post():
            return 'Create Post'

    The current user must have either the `editor` role or `author` role in
    order to view the page.

    :param args: The possible roles.
    """
    perm = Permission(*[RoleNeed(role) for role in roles])

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated():
                login_view = app.security.login_manager.login_view
                return redirect(login_url(login_view, request.url))

            if perm.can():
                return fn(*args, **kwargs)

            r1 = [r for r in roles]
            r2 = [r.name for r in current_user.roles]

            app.logger.debug('Current user does not provide a '
                'required role. Accepted: %s Provided: %s' % (r1, r2))

            utils.do_flash('You do not have permission to '
                           'view this resource', 'error')

            return redirect(request.referrer or '/')
        return decorated_view
    return wrapper

# -*- coding: utf-8 -*-
"""
    test_hashing
    ~~~~~~~~~~~~

    hashing tests
"""

from pytest import raises
from utils import authenticate, init_app_with_options
from passlib.hash import pbkdf2_sha256, django_pbkdf2_sha256, plaintext

from flask_security.utils import hash_password, verify_password, get_hmac


def test_verify_password_bcrypt_double_hash(app, sqlalchemy_datastore):
    init_app_with_options(app, sqlalchemy_datastore, **{
        'SECURITY_PASSWORD_HASH': 'bcrypt',
        'SECURITY_PASSWORD_SALT': 'salty',
        'SECURITY_PASSWORD_SINGLE_HASH': False,
    })
    with app.app_context():
        assert verify_password('pass', hash_password('pass'))


def test_verify_password_bcrypt_single_hash(app, sqlalchemy_datastore):
    init_app_with_options(app, sqlalchemy_datastore, **{
        'SECURITY_PASSWORD_HASH': 'bcrypt',
        'SECURITY_PASSWORD_SALT': None,
        'SECURITY_PASSWORD_SINGLE_HASH': True,
    })
    with app.app_context():
        assert verify_password('pass', hash_password('pass'))


def test_verify_password_single_hash_list(app, sqlalchemy_datastore):
    init_app_with_options(app, sqlalchemy_datastore, **{
        'SECURITY_PASSWORD_HASH': 'bcrypt',
        'SECURITY_PASSWORD_SALT': 'salty',
        'SECURITY_PASSWORD_SINGLE_HASH': ['django_pbkdf2_sha256', 'plaintext'],
        'SECURITY_PASSWORD_SCHEMES': [
            'bcrypt', 'pbkdf2_sha256', 'django_pbkdf2_sha256', 'plaintext'
        ]
    })
    with app.app_context():
        # double hash
        assert verify_password('pass', hash_password('pass'))
        assert verify_password('pass', pbkdf2_sha256.hash(get_hmac('pass')))
        # single hash
        assert verify_password('pass', django_pbkdf2_sha256.hash('pass'))
        assert verify_password('pass', plaintext.hash('pass'))


def test_verify_password_backward_compatibility(app, sqlalchemy_datastore):
    init_app_with_options(app, sqlalchemy_datastore, **{
        'SECURITY_PASSWORD_HASH': 'bcrypt',
        'SECURITY_PASSWORD_SINGLE_HASH': False,
        'SECURITY_PASSWORD_SCHEMES': ['bcrypt', 'plaintext']
    })
    with app.app_context():
        # double hash
        assert verify_password('pass', hash_password('pass'))
        # single hash
        assert verify_password('pass', plaintext.hash('pass'))


def test_verify_password_bcrypt_rounds_too_low(app, sqlalchemy_datastore):
    with raises(ValueError) as exc_msg:
        init_app_with_options(app, sqlalchemy_datastore, **{
            'SECURITY_PASSWORD_HASH': 'bcrypt',
            'SECURITY_PASSWORD_SALT': 'salty',
            'SECURITY_PASSWORD_HASH_OPTIONS': {'bcrypt': {'rounds': 3}}
        })
    assert all(s in str(exc_msg) for s in ['rounds', 'too low'])


def test_login_with_bcrypt_enabled(app, sqlalchemy_datastore):
    init_app_with_options(app, sqlalchemy_datastore, **{
        'SECURITY_PASSWORD_HASH': 'bcrypt',
        'SECURITY_PASSWORD_SALT': 'salty',
        'SECURITY_PASSWORD_SINGLE_HASH': False,
    })
    response = authenticate(app.test_client(), follow_redirects=True)
    assert b'Home Page' in response.data


def test_missing_hash_salt_option(app, sqlalchemy_datastore):
    with raises(RuntimeError):
        init_app_with_options(app, sqlalchemy_datastore, **{
            'SECURITY_PASSWORD_HASH': 'bcrypt',
            'SECURITY_PASSWORD_SALT': None,
            'SECURITY_PASSWORD_SINGLE_HASH': False,
        })

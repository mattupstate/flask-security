# -*- coding: utf-8 -*-
"""
    test_cache
    ~~~~~~~~~~~~

    verify hash cache tests
"""

from flask_security.cache import VerifyHashCache
from flask_security.core import _request_loader, local_cache


class MockRequest:
    @property
    def headers(self):
        return {"token-header": "mock-token-header"}

    @property
    def args(self):
        return {}

    @property
    def is_json(self):
        return True

    def get_json(self, silent=None):
        return {}


class MockUser:
    def __init__(self, id, password):
        self.id = id
        self.password = password


class MockExtensionSecurity:
    @property
    def token_authentication_header(self):
        return "token-header"

    @property
    def token_authentication_key(self):
        return "token-key"

    @property
    def login_manager(self):
        class MockLoginManager:
            def anonymous_user(self):
                return None

        return MockLoginManager()

    @property
    def remember_token_serializer(self):
        class MockLoader:
            def loads(self, token, max_age):
                return [1, "token"]

        return MockLoader()

    @property
    def token_max_age(self):
        return 1

    @property
    def datastore(self):
        class MockDataStore:
            def find_user(self, id=None):
                return MockUser(id, "token")

        return MockDataStore()

    @property
    def hashing_context(self):
        class MockHashingContext:
            def verify(self, encoded_data, hashed_data):
                return encoded_data.decode() == hashed_data

        return MockHashingContext()


def test_verify_password_cache_init(app):
    with app.app_context():
        vhc = VerifyHashCache()
        assert len(vhc._cache) == 0
        assert vhc._cache.ttl == 60 * 5
        assert vhc._cache.maxsize == 500
        app.config["VERIFY_HASH_CACHE_TTL"] = 10
        app.config["VERIFY_HASH_CACHE_MAX_SIZE"] = 10
        vhc = VerifyHashCache()
        assert vhc._cache.ttl == 10
        assert vhc._cache.maxsize == 10


def test_verify_password_cache_set_get(app):
    class MockUser:
        def __init__(self, id):
            self.id = id

    user = MockUser(1)
    with app.app_context():
        vhc = VerifyHashCache()
        assert vhc.has_verify_hash_cache(user) is None
        vhc.set_cache(user)
        assert len(vhc._cache) == 1
        assert vhc.has_verify_hash_cache(user)
        vhc.clear()
        assert vhc.has_verify_hash_cache(user) is None


def test_request_loader_not_using_cache(app):
    with app.app_context():
        app.extensions["security"] = MockExtensionSecurity()
        _request_loader(MockRequest())
        assert getattr(local_cache, "verify_hash_cache", None) is None


def test_request_loader_using_cache(app):
    with app.app_context():
        app.config["USE_VERIFY_PASSWORD_CACHE"] = True
        app.extensions["security"] = MockExtensionSecurity()
        _request_loader(MockRequest())
        assert local_cache.verify_hash_cache is not None
        assert local_cache.verify_hash_cache.has_verify_hash_cache(MockUser(1, "token"))

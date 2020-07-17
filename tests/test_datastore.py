# -*- coding: utf-8 -*-
"""
    test_datastore
    ~~~~~~~~~~~~~~

    Datastore tests
"""

from pytest import raises
from utils import init_app_with_options

from flask_security import RoleMixin, Security, UserMixin
from flask_security.datastore import Datastore, UserDatastore


class User(UserMixin):
    pass


class Role(RoleMixin):
    pass


class FakeUserDatastore(UserDatastore):
    def find_role(self, role_name):
        return role_name if role_name != 'lordofchaos' else None


class FakeUserModel(object):
    roles = 'ABC'


class FakeUserModelWithoutRoles(object):
    pass


def test_unimplemented_datastore_methods():
    datastore = Datastore(None)
    assert datastore.db is None
    with raises(NotImplementedError):
        datastore.put(None)
    with raises(NotImplementedError):
        datastore.delete(None)
    assert not datastore.commit()


def test_unimplemented_user_datastore_methods():
    datastore = UserDatastore(None, None)
    with raises(NotImplementedError):
        datastore.find_user(None)
    with raises(NotImplementedError):
        datastore.find_role(None)
    with raises(NotImplementedError):
        datastore.get_user(None)


def test_toggle_active():
    datastore = UserDatastore(None, None)
    user = User()
    user.active = True
    assert datastore.toggle_active(user) is True
    assert not user.active
    assert datastore.toggle_active(user) is True
    assert user.active is True


def test_deactivate_user():
    datastore = UserDatastore(None, None)
    user = User()
    user.active = True
    assert datastore.deactivate_user(user) is True
    assert not user.active


def test_activate_user():
    datastore = UserDatastore(None, None)
    user = User()
    user.active = False
    assert datastore.activate_user(user) is True
    assert user.active is True


def test_deactivate_returns_false_if_already_false():
    datastore = UserDatastore(None, None)
    user = User()
    user.active = False
    assert not datastore.deactivate_user(user)


def test_activate_returns_false_if_already_true():
    datastore = UserDatastore(None, None)
    user = User()
    user.active = True
    assert not datastore.activate_user(user)


def test_get_user(app, datastore):
    init_app_with_options(app, datastore, **{
        'SECURITY_USER_IDENTITY_ATTRIBUTES': ('email', 'username')
    })

    with app.app_context():
        user_id = datastore.find_user(email='matt@lp.com').id

        user = datastore.get_user(user_id)
        assert user is not None

        user = datastore.get_user('matt@lp.com')
        assert user is not None

        user = datastore.get_user('matt')
        assert user is not None

        # Regression check
        user = datastore.get_user('%lp.com')
        assert user is None


def test_find_role(app, datastore):
    init_app_with_options(app, datastore)

    with app.app_context():
        role = datastore.find_role('admin')
        assert role is not None

        role = datastore.find_role('bogus')
        assert role is None


def test_add_role_to_user(app, datastore):
    init_app_with_options(app, datastore)

    with app.app_context():
        # Test with user object
        user = datastore.find_user(email='matt@lp.com')
        assert user.has_role('editor') is False
        assert datastore.add_role_to_user(user, 'editor') is True
        assert datastore.add_role_to_user(user, 'editor') is False
        assert user.has_role('editor') is True

        # Test with email
        assert datastore.add_role_to_user('jill@lp.com', 'editor') is True
        user = datastore.find_user(email='jill@lp.com')
        assert user.has_role('editor') is True

        # Test remove role
        assert datastore.remove_role_from_user(user, 'editor') is True
        assert datastore.remove_role_from_user(user, 'editor') is False


def test_create_user_with_roles(app, datastore):
    init_app_with_options(app, datastore)

    with app.app_context():
        role = datastore.find_role('admin')
        datastore.commit()

        user = datastore.create_user(email='dude@lp.com', username='dude',
                                     password='password', roles=[role])
        datastore.commit()
        user = datastore.find_user(email='dude@lp.com')
        assert user.has_role('admin') is True


def test_delete_user(app, datastore):
    init_app_with_options(app, datastore)

    with app.app_context():
        user = datastore.find_user(email='matt@lp.com')
        datastore.delete_user(user)
        datastore.commit()
        user = datastore.find_user(email='matt@lp.com')
        assert user is None


def test_access_datastore_from_factory(app, datastore):
    security = Security()
    security.init_app(app, datastore)

    assert security.datastore is not None
    assert security.app is not None


def test_access_datastore_from_app_factory_pattern(app, datastore):
    security = Security(datastore=datastore)
    security.init_app(app)

    assert security.datastore is not None
    assert security.app is not None


def test_init_app_kwargs_override_constructor_kwargs(app, datastore):
    security = Security(datastore=datastore, login_form='__init__login_form',
                        register_form='__init__register_form')
    security.init_app(app, login_form='init_app_login_form')

    assert security.login_form == 'init_app_login_form'
    assert security.register_form == '__init__register_form'


def test_prepare_create_user_args_with_roles():
    datastore = FakeUserDatastore(FakeUserModel(), type(None))
    roles = ['godofthunder', 'lordofchaos', 'majordufus']

    create_kwargs = datastore._prepare_create_user_args(roles=roles)

    assert create_kwargs == {
        'active': True, 'roles': ['godofthunder', 'majordufus']}


def test_prepare_create_user_args_without_roles():
    datastore = FakeUserDatastore(FakeUserModel(), type(None))

    create_kwargs = datastore._prepare_create_user_args(active=False)

    assert create_kwargs == {'active': False}


def test_prepare_create_user_args_without_usermodel_roles():
    datastore = FakeUserDatastore(FakeUserModelWithoutRoles(), type(None))

    with raises(ValueError):
        datastore._prepare_create_user_args(roles=['hippotamer'])

# -*- coding: utf-8 -*-
"""
    flask_security.datastore
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains an user datastore classes.

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from .utils import get_identity_attributes, string_types


class Datastore(object):
    def __init__(self, db):
        self.db = db

    def commit(self):
        pass

    def put(self, model):
        raise NotImplementedError

    def delete(self, model):
        raise NotImplementedError


class SQLAlchemyDatastore(Datastore):
    def commit(self):
        self.db.session.commit()

    def put(self, model):
        self.db.session.add(model)
        return model

    def delete(self, model):
        self.db.session.delete(model)


class MongoEngineDatastore(Datastore):
    def put(self, model):
        model.save()
        return model

    def delete(self, model):
        model.delete()


class PeeweeDatastore(Datastore):
    def put(self, model):
        model.save()
        return model

    def delete(self, model):
        model.delete_instance(recursive=True)


def with_pony_session(f):
    from functools import wraps

    @wraps(f)
    def decorator(*args, **kwargs):
        from pony.orm import db_session
        from pony.orm.core import local
        from flask import after_this_request, current_app, has_app_context, \
            has_request_context
        from flask.signals import appcontext_popped

        register = local.db_context_counter == 0
        if register and (has_app_context() or has_request_context()):
            db_session.__enter__()

        result = f(*args, **kwargs)

        if register:
            if has_request_context():
                @after_this_request
                def pop(request):
                    db_session.__exit__()
                    return request
            elif has_app_context():
                @appcontext_popped.connect_via(
                    current_app._get_current_object()
                )
                def pop(sender, *args, **kwargs):
                    while local.db_context_counter:
                        db_session.__exit__()
            else:
                raise RuntimeError('Needs app or request context')
        return result
    return decorator


class PonyDatastore(Datastore):
    def commit(self):
        self.db.commit()

    @with_pony_session
    def put(self, model):
        return model

    @with_pony_session
    def delete(self, model):
        model.delete()


class UserDatastore(object):
    """Abstracted user datastore.

    :param user_model: A user model class definition
    :param role_model: A role model class definition
    """

    def __init__(self, user_model, role_model):
        self.user_model = user_model
        self.role_model = role_model

    def _prepare_role_modify_args(self, user, role):
        if isinstance(user, string_types):
            user = self.find_user(email=user)
        if isinstance(role, string_types):
            role = self.find_role(role)
        return user, role

    def _prepare_create_user_args(self, **kwargs):
        kwargs.setdefault('active', True)
        roles = kwargs.get('roles', [])

        if not hasattr(self.user_model, 'roles') and roles:
            raise ValueError((
                'Cannot create user with roles %s, because the user '
                'model has no "roles" attribute') % str(roles))

        if roles:
            roles_to_add = []

            for role in roles:
                rn = role.name if isinstance(role, self.role_model) else role

                # see if the role exists
                role_to_add = self.find_role(rn)

                if role_to_add:
                    roles_to_add.append(role_to_add)

            kwargs['roles'] = roles_to_add

        return kwargs

    def get_user(self, id_or_email):
        """Returns a user matching the specified ID or email address."""
        raise NotImplementedError

    def find_user(self, *args, **kwargs):
        """Returns a user matching the provided parameters."""
        raise NotImplementedError

    def find_role(self, *args, **kwargs):
        """Returns a role matching the provided name."""
        raise NotImplementedError

    def add_role_to_user(self, user, role):
        """Adds a role to a user.

        :param user: The user to manipulate
        :param role: The role to add to the user
        """
        user, role = self._prepare_role_modify_args(user, role)
        if role not in user.roles:
            user.roles.append(role)
            self.put(user)
            return True
        return False

    def remove_role_from_user(self, user, role):
        """Removes a role from a user.

        :param user: The user to manipulate
        :param role: The role to remove from the user
        """
        rv = False
        user, role = self._prepare_role_modify_args(user, role)
        if role in user.roles:
            rv = True
            user.roles.remove(role)
            self.put(user)
        return rv

    def toggle_active(self, user):
        """Toggles a user's active status. Always returns True."""
        user.active = not user.active
        return True

    def deactivate_user(self, user):
        """Deactivates a specified user. Returns `True` if a change was made.

        :param user: The user to deactivate
        """
        if user.active:
            user.active = False
            return True
        return False

    def activate_user(self, user):
        """Activates a specified user. Returns `True` if a change was made.

        :param user: The user to activate
        """
        if not user.active:
            user.active = True
            return True
        return False

    def create_role(self, **kwargs):
        """Creates and returns a new role from the given parameters."""

        role = self.role_model(**kwargs)
        return self.put(role)

    def find_or_create_role(self, name, **kwargs):
        """Returns a role matching the given name or creates it with any
        additionally provided parameters.
        """
        kwargs["name"] = name
        return self.find_role(name) or self.create_role(**kwargs)

    def create_user(self, **kwargs):
        """Creates and returns a new user from the given parameters."""
        kwargs = self._prepare_create_user_args(**kwargs)
        user = self.user_model(**kwargs)
        return self.put(user)

    def delete_user(self, user):
        """Deletes the specified user.

        :param user: The user to delete
        """
        self.delete(user)


class SQLAlchemyUserDatastore(SQLAlchemyDatastore, UserDatastore):
    """A SQLAlchemy datastore implementation for Flask-Security that assumes the
    use of the Flask-SQLAlchemy extension.
    """
    def __init__(self, db, user_model, role_model):
        SQLAlchemyDatastore.__init__(self, db)
        UserDatastore.__init__(self, user_model, role_model)

    def get_user(self, identifier):
        from sqlalchemy import func as alchemyFn
        user_model_query = self.user_model.query
        if hasattr(self.user_model, 'roles'):
            from sqlalchemy.orm import joinedload
            user_model_query = user_model_query.options(joinedload('roles'))

        if self._is_numeric(identifier):
            return user_model_query.get(identifier)
        for attr in get_identity_attributes():
            query = alchemyFn.lower(getattr(self.user_model, attr)) \
                == alchemyFn.lower(identifier)
            rv = user_model_query.filter(query).first()
            if rv is not None:
                return rv

    def _is_numeric(self, value):
        try:
            int(value)
        except (TypeError, ValueError):
            return False
        return True

    def find_user(self, **kwargs):
        query = self.user_model.query
        if hasattr(self.user_model, 'roles'):
            from sqlalchemy.orm import joinedload
            query = query.options(joinedload('roles'))

        return query.filter_by(**kwargs).first()

    def find_role(self, role):
        return self.role_model.query.filter_by(name=role).first()


class SQLAlchemySessionUserDatastore(SQLAlchemyUserDatastore,
                                     SQLAlchemyDatastore):
    """A SQLAlchemy datastore implementation for Flask-Security that assumes the
    use of the flask_sqlalchemy_session extension.
    """
    def __init__(self, session, user_model, role_model):

        class PretendFlaskSQLAlchemyDb(object):
            """ This is a pretend db object, so we can just pass in a session.
            """
            def __init__(self, session):
                self.session = session

        SQLAlchemyUserDatastore.__init__(self,
                                         PretendFlaskSQLAlchemyDb(session),
                                         user_model,
                                         role_model)

    def commit(self):
        # Old flask-sqlalchemy adds this weird attribute for tracking
        # to Session. flask-sqlalchemy 2.0 does things more nicely.
        try:
            super(SQLAlchemySessionUserDatastore, self).commit()
        except AttributeError:
            import sqlalchemy
            sqlalchemy.orm.Session._model_changes = {}
            super(SQLAlchemySessionUserDatastore, self).commit()


class MongoEngineUserDatastore(MongoEngineDatastore, UserDatastore):
    """A MongoEngine datastore implementation for Flask-Security that assumes
    the use of the Flask-MongoEngine extension.
    """
    def __init__(self, db, user_model, role_model):
        MongoEngineDatastore.__init__(self, db)
        UserDatastore.__init__(self, user_model, role_model)

    def get_user(self, identifier):
        from mongoengine import ValidationError
        try:
            return self.user_model.objects(id=identifier).first()
        except (ValidationError, ValueError):
            pass
        for attr in get_identity_attributes():
            query_key = '%s__iexact' % attr
            query = {query_key: identifier}
            rv = self.user_model.objects(**query).first()
            if rv is not None:
                return rv

    def find_user(self, **kwargs):
        try:
            from mongoengine.queryset import Q, QCombination
        except ImportError:
            from mongoengine.queryset.visitor import Q, QCombination
        from mongoengine.errors import ValidationError

        queries = map(lambda i: Q(**{i[0]: i[1]}), kwargs.items())
        query = QCombination(QCombination.AND, queries)
        try:
            return self.user_model.objects(query).first()
        except ValidationError:  # pragma: no cover
            return None

    def find_role(self, role):
        return self.role_model.objects(name=role).first()

    # TODO: Not sure why this was added but tests pass without it
    # def add_role_to_user(self, user, role):
    #     rv = super(MongoEngineUserDatastore, self).add_role_to_user(
    #         user, role)
    #     if rv:
    #         self.put(user)
    #     return rv


class PeeweeUserDatastore(PeeweeDatastore, UserDatastore):
    """A PeeweeD datastore implementation for Flask-Security that assumes
    the use of the Flask-Peewee extension.

    :param user_model: A user model class definition
    :param role_model: A role model class definition
    :param role_link: A model implementing the many-to-many user-role relation
    """
    def __init__(self, db, user_model, role_model, role_link):
        PeeweeDatastore.__init__(self, db)
        UserDatastore.__init__(self, user_model, role_model)
        self.UserRole = role_link

    def get_user(self, identifier):
        from peewee import fn as peeweeFn
        try:
            return self.user_model.get(self.user_model.id == identifier)
        except ValueError:
            pass

        for attr in get_identity_attributes():
            column = getattr(self.user_model, attr)
            try:
                return self.user_model.get(
                    peeweeFn.Lower(column) == peeweeFn.Lower(identifier))
            except self.user_model.DoesNotExist:
                pass

    def find_user(self, **kwargs):
        try:
            return self.user_model.filter(**kwargs).get()
        except self.user_model.DoesNotExist:
            return None

    def find_role(self, role):
        try:
            return self.role_model.filter(name=role).get()
        except self.role_model.DoesNotExist:
            return None

    def create_user(self, **kwargs):
        """Creates and returns a new user from the given parameters."""
        roles = kwargs.pop('roles', [])
        user = self.user_model(**self._prepare_create_user_args(**kwargs))
        user = self.put(user)
        for role in roles:
            self.add_role_to_user(user, role)
        self.put(user)
        return user

    def add_role_to_user(self, user, role):
        """Adds a role to a user.

        :param user: The user to manipulate
        :param role: The role to add to the user
        """
        user, role = self._prepare_role_modify_args(user, role)
        result = self.UserRole.select().where(
            self.UserRole.user == user.id,
            self.UserRole.role == role.id,
        )
        if result.count():
            return False
        else:
            self.put(self.UserRole.create(user=user.id, role=role.id))
            return True

    def remove_role_from_user(self, user, role):
        """Removes a role from a user.

        :param user: The user to manipulate
        :param role: The role to remove from the user
        """
        user, role = self._prepare_role_modify_args(user, role)
        result = self.UserRole.select().where(
            self.UserRole.user == user,
            self.UserRole.role == role,
        )
        if result.count():
            query = self.UserRole.delete().where(
                self.UserRole.user == user, self.UserRole.role == role)
            query.execute()
            return True
        else:
            return False


class PonyUserDatastore(PonyDatastore, UserDatastore):
    """A Pony ORM datastore implementation for Flask-Security.

    Code primarily from https://github.com/ET-CS but taken over after
    being abandoned.
    """

    def __init__(self, db, user_model, role_model):
        PonyDatastore.__init__(self, db)
        UserDatastore.__init__(self, user_model, role_model)

    @with_pony_session
    def get_user(self, identifier):
        if self._is_numeric(identifier):
            return self.user_model[identifier]

        for attr in get_identity_attributes():
            # this is a nightmare, tl;dr we need to get the thing that
            # corresponds to email (usually)
            user = self.user_model.get(**{attr: identifier})
            if user is not None:
                return user

    def _is_numeric(self, value):
        try:
            int(value)
        except ValueError:
            return False
        return True

    @with_pony_session
    def find_user(self, **kwargs):
        return self.user_model.get(**kwargs)

    @with_pony_session
    def find_role(self, role):
        return self.role_model.get(name=role)

    @with_pony_session
    def add_role_to_user(self, *args, **kwargs):
        return super(PonyUserDatastore, self).add_role_to_user(*args, **kwargs)

    @with_pony_session
    def create_user(self, **kwargs):
        return super(PonyUserDatastore, self).create_user(**kwargs)

    @with_pony_session
    def create_role(self, **kwargs):
        return super(PonyUserDatastore, self).create_role(**kwargs)

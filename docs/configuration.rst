Configuration
=============

The following configuration values are used by Flask-Security:

Core
--------------

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|

======================================== =======================================
``SECURITY_BLUEPRINT_NAME``              Specifies the name for the
                                         Flask-Security blueprint. Defaults to
                                         ``security``.
``SECURITY_CLI_USERS_NAME``              Specifies the name for the command
                                         managing users. Disable by setting
                                         ``False``. Defaults to ``users``.
``SECURITY_CLI_ROLES_NAME``              Specifies the name for the command
                                         managing roles. Disable by setting
                                         ``False``. Defaults to ``roles``.
``SECURITY_URL_PREFIX``                  Specifies the URL prefix for the
                                         Flask-Security blueprint. Defaults to
                                         ``None``.
``SECURITY_SUBDOMAIN``                   Specifies the subdomain for the
                                         Flask-Security blueprint. Defaults to
                                         ``None``.
``SECURITY_FLASH_MESSAGES``              Specifies whether or not to flash
                                         messages during security procedures.
                                         Defaults to ``True``.
``SECURITY_I18N_DOMAIN``                 Specifies the name for domain
                                         used for translations.
                                         Defaults to ``flask_security``.
``SECURITY_I18N_DIRNAME``                Specifies the directory containing the
                                         ``MO`` files used for translations.
                                         Defaults to
                                         ``[PATH_LIB]/flask_security/translations``.
``SECURITY_PASSWORD_HASH``               Specifies the password hash algorithm to
                                         use when hashing passwords. Recommended
                                         values for production systems are
                                         ``bcrypt``, ``sha512_crypt``, or
                                         ``pbkdf2_sha512``. Defaults to
                                         ``bcrypt``.
``SECURITY_PASSWORD_SALT``               Specifies the HMAC salt. This is only
                                         used if the password hash type is set
                                         to something other than plain text.
                                         Defaults to ``None``.
``SECURITY_PASSWORD_SINGLE_HASH``        Specifies that passwords should only be
                                         hashed once. By default, passwords are
                                         hashed twice, first with
                                         ``SECURITY_PASSWORD_SALT``, and then
                                         with a random salt. May be useful for
                                         integrating with other applications.
                                         It can also be a set of scheme that
                                         should not be hashed twice.
                                         Default to a list of known schemes
                                         not working with double hashing
                                         (`django_{digest}`, `plaintext`).
                                         Defaults to ``False``.
``SECURITY_HASHING_SCHEMES``             List of algorithms used for
                                         creating and validating tokens.
                                         Defaults to ``sha256_crypt``.
``SECURITY_DEPRECATED_HASHING_SCHEMES``  List of deprecated algorithms used for
                                         creating and validating tokens.
                                         Defaults to ``hex_md5``.
``SECURITY_PASSWORD_HASH_OPTIONS``       Specifies additional options to be passed
                                         to the hashing method.
``SECURITY_EMAIL_SENDER``                Specifies the email address to send
                                         emails as. Defaults to value set
                                         to ``MAIL_DEFAULT_SENDER`` if
                                         Flask-Mail is used otherwise
                                         ``no-reply@localhost``.
``SECURITY_TOKEN_AUTHENTICATION_KEY``    Specifies the query string parameter to
                                         read when using token authentication.
                                         Defaults to ``auth_token``.
``SECURITY_TOKEN_AUTHENTICATION_HEADER`` Specifies the HTTP header to read when
                                         using token authentication. Defaults to
                                         ``Authentication-Token``.
``SECURITY_TOKEN_MAX_AGE``               Specifies the number of seconds before
                                         an authentication token expires.
                                         Defaults to None, meaning the token
                                         never expires.
``SECURITY_DEFAULT_HTTP_AUTH_REALM``     Specifies the default authentication
                                         realm when using basic HTTP auth.
                                         Defaults to ``Login Required``
======================================== =======================================


URLs and Views
--------------

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|

=============================== ================================================
``SECURITY_LOGIN_URL``          Specifies the login URL. Defaults to ``/login``.
``SECURITY_LOGOUT_URL``         Specifies the logout URL. Defaults to
                                ``/logout``.
``SECURITY_REGISTER_URL``       Specifies the register URL. Defaults to
                                ``/register``.
``SECURITY_RESET_URL``          Specifies the password reset URL. Defaults to
                                ``/reset``.
``SECURITY_CHANGE_URL``         Specifies the password change URL. Defaults to
                                ``/change``.
``SECURITY_CONFIRM_URL``        Specifies the email confirmation URL. Defaults
                                to ``/confirm``.
``SECURITY_POST_LOGIN_VIEW``    Specifies the default view to redirect to after
                                a user logs in. This value can be set to a URL
                                or an endpoint name. Defaults to ``/``.
``SECURITY_POST_LOGOUT_VIEW``   Specifies the default view to redirect to after
                                a user logs out. This value can be set to a URL
                                or an endpoint name. Defaults to ``/``.
``SECURITY_CONFIRM_ERROR_VIEW`` Specifies the view to redirect to if a
                                confirmation error occurs. This value can be set
                                to a URL or an endpoint name. If this value is
                                ``None``, the user is presented the default view
                                to resend a confirmation link. Defaults to
                                ``None``.
``SECURITY_POST_REGISTER_VIEW`` Specifies the view to redirect to after a user
                                successfully registers. This value can be set to
                                a URL or an endpoint name. If this value is
                                ``None``, the user is redirected to the value of
                                ``SECURITY_POST_LOGIN_VIEW``. Defaults to
                                ``None``.
``SECURITY_POST_CONFIRM_VIEW``  Specifies the view to redirect to after a user
                                successfully confirms their email. This value
                                can be set to a URL or an endpoint name. If this
                                value is ``None``, the user is redirected  to the
                                value of ``SECURITY_POST_LOGIN_VIEW``. Defaults
                                to ``None``.
``SECURITY_POST_RESET_VIEW``    Specifies the view to redirect to after a user
                                successfully resets their password. This value
                                can be set to a URL or an endpoint name. If this
                                value is ``None``, the user is redirected  to the
                                value of ``SECURITY_POST_LOGIN_VIEW``. Defaults
                                to ``None``.
``SECURITY_POST_CHANGE_VIEW``   Specifies the view to redirect to after a user
                                successfully changes their password. This value
                                can be set to a URL or an endpoint name. If this
                                value is ``None``, the user is redirected  to the
                                value of ``SECURITY_POST_LOGIN_VIEW``. Defaults
                                to ``None``.
``SECURITY_UNAUTHORIZED_VIEW``  Specifies the view to redirect to if a user
                                attempts to access a URL/endpoint that they do
                                not have permission to access. If this value is
                                ``None``, the user is presented with a default
                                HTTP 403 response. Defaults to ``None``.
=============================== ================================================


Template Paths
--------------

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|

======================================== =======================================
``SECURITY_FORGOT_PASSWORD_TEMPLATE``    Specifies the path to the template for
                                         the forgot password page. Defaults to
                                         ``security/forgot_password.html``.
``SECURITY_LOGIN_USER_TEMPLATE``         Specifies the path to the template for
                                         the user login page. Defaults to
                                         ``security/login_user.html``.
``SECURITY_REGISTER_USER_TEMPLATE``      Specifies the path to the template for
                                         the user registration page. Defaults to
                                         ``security/register_user.html``.
``SECURITY_RESET_PASSWORD_TEMPLATE``     Specifies the path to the template for
                                         the reset password page. Defaults to
                                         ``security/reset_password.html``.
``SECURITY_CHANGE_PASSWORD_TEMPLATE``    Specifies the path to the template for
                                         the change password page. Defaults to
                                         ``security/change_password.html``.
``SECURITY_SEND_CONFIRMATION_TEMPLATE``  Specifies the path to the template for
                                         the resend confirmation instructions
                                         page. Defaults to
                                         ``security/send_confirmation.html``.
``SECURITY_SEND_LOGIN_TEMPLATE``         Specifies the path to the template for
                                         the send login instructions page for
                                         passwordless logins. Defaults to
                                         ``security/send_login.html``.
======================================== =======================================


Feature Flags
-------------

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|

========================= ======================================================
``SECURITY_CONFIRMABLE``  Specifies if users are required to confirm their email
                          address when registering a new account. If this value
                          is `True`, Flask-Security creates an endpoint to handle
                          confirmations and requests to resend confirmation
                          instructions. The URL for this endpoint is specified
                          by the ``SECURITY_CONFIRM_URL`` configuration option.
                          Defaults to ``False``.
``SECURITY_REGISTERABLE`` Specifies if Flask-Security should create a user
                          registration endpoint. The URL for this endpoint is
                          specified by the ``SECURITY_REGISTER_URL``
                          configuration option. Defaults to ``False``.
``SECURITY_RECOVERABLE``  Specifies if Flask-Security should create a password
                          reset/recover endpoint. The URL for this endpoint is
                          specified by the ``SECURITY_RESET_URL`` configuration
                          option. Defaults to ``False``.
``SECURITY_TRACKABLE``    Specifies if Flask-Security should track basic user
                          login statistics. If set to ``True``, ensure your
                          models have the required fields/attributes. Be sure to
                          use `ProxyFix <http://flask.pocoo.org/docs/0.10/deploying/wsgi-standalone/#proxy-setups>`_ if you are using a proxy. Defaults to
                          ``False``
``SECURITY_PASSWORDLESS`` Specifies if Flask-Security should enable the
                          passwordless login feature. If set to ``True``, users
                          are not required to enter a password to login but are
                          sent an email with a login link. This feature is
                          experimental and should be used with caution. Defaults
                          to ``False``.
``SECURITY_CHANGEABLE``   Specifies if Flask-Security should enable the
                          change password endpoint. The URL for this endpoint is
                          specified by the ``SECURITY_CHANGE_URL`` configuration
                          option. Defaults to ``False``.
``SECURITY_LOGINABLE``    Specifies if Flask-Security should enable the login
                          endpoint. The URL for this endpoint is specified by
                          the ``SECURITY_LOGIN_URL`` configuration option.
                          This should generally be left enabled, unless you
                          want to use a custom login endpoint instead of the one
                          provided by Flask-Security. Note that this flag
                          does not affect whether or not authentication is
                          enforced across your site's views. For controlling
                          that, refer to the ``LOGIN_DISABLED`` flag for
                          Flask-Login. Defaults to ``True``.
``SECURITY_LOGOUTABLE`    Specifies if Flask-Security should enable the logout
                          endpoint. The URL for this endpoint is specified by
                          the ``SECURITY_LOGOUT_URL`` configuration option.
                          This should generally be left enabled, unless you
                          want to use a custom logout endpoint instead of the
                          one provided by Flask-Security. Note that this flag
                          does not affect whether or not authentication is
                          enforced across your site's views. For controlling
                          that, refer to the ``LOGIN_DISABLED`` flag for
                          Flask-Login. Defaults to ``True``.
========================= ======================================================

Email
----------

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|

================================================= ==============================
``SECURITY_EMAIL_SUBJECT_REGISTER``               Sets the subject for the
                                                  confirmation email. Defaults
                                                  to ``Welcome``
``SECURITY_EMAIL_SUBJECT_PASSWORDLESS``           Sets the subject for the
                                                  passwordless feature. Defaults
                                                  to ``Login instructions``
``SECURITY_EMAIL_SUBJECT_PASSWORD_NOTICE``        Sets subject for the password
                                                  notice. Defaults to ``Your
                                                  password has been reset``
``SECURITY_EMAIL_SUBJECT_PASSWORD_RESET``         Sets the subject for the
                                                  password reset email. Defaults
                                                  to ``Password reset
                                                  instructions``
``SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE`` Sets the subject for the
                                                  password change notice.
                                                  Defaults to ``Your password
                                                  has been changed``
``SECURITY_EMAIL_SUBJECT_CONFIRM``                Sets the subject for the email
                                                  confirmation message. Defaults
                                                  to ``Please confirm your
                                                  email``
``SECURITY_EMAIL_PLAINTEXT``                      Sends email as plaintext using
                                                  ``*.txt`` template. Defaults
                                                  to ``True``.
``SECURITY_EMAIL_HTML``                           Sends email as HTML using
                                                  ``*.html`` template. Defaults
                                                  to ``True``.
================================================= ==============================

Miscellaneous
-------------

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|

============================================= ==================================
``SECURITY_USER_IDENTITY_ATTRIBUTES``         Specifies which attributes of the
                                              user object can be used for login.
                                              Defaults to ``['email']``.
``SECURITY_SEND_REGISTER_EMAIL``              Specifies whether registration
                                              email is sent. Defaults to
                                              ``True``.
``SECURITY_SEND_PASSWORD_CHANGE_EMAIL``       Specifies whether password change
                                              email is sent. Defaults to
                                              ``True``.
``SECURITY_SEND_PASSWORD_RESET_EMAIL``        Specifies whether password reset
                                              email is sent. Defaults to
                                              ``True``.
``SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL`` Specifies whether password reset
                                              notice email is sent. Defaults to
                                              ``True``.

``SECURITY_CONFIRM_EMAIL_WITHIN``             Specifies the amount of time a
                                              user has before their confirmation
                                              link expires. Always pluralized
                                              the time unit for this value.
                                              Defaults to ``5 days``.
``SECURITY_RESET_PASSWORD_WITHIN``            Specifies the amount of time a
                                              user has before their password
                                              reset link expires. Always
                                              pluralized the time unit for this
                                              value. Defaults to ``5 days``.
``SECURITY_LOGIN_WITHIN``                     Specifies the amount of time a
                                              user has before a login link
                                              expires. This is only used when
                                              the passwordless login feature is
                                              enabled. Always pluralized the
                                              time unit for this value.
                                              Defaults to ``1 days``.
``SECURITY_LOGIN_WITHOUT_CONFIRMATION``       Specifies if a user may login
                                              before confirming their email when
                                              the value of
                                              ``SECURITY_CONFIRMABLE`` is set to
                                              ``True``. Defaults to ``False``.
``SECURITY_CONFIRM_SALT``                     Specifies the salt value when
                                              generating confirmation
                                              links/tokens. Defaults to
                                              ``confirm-salt``.
``SECURITY_RESET_SALT``                       Specifies the salt value when
                                              generating password reset
                                              links/tokens. Defaults to
                                              ``reset-salt``.
``SECURITY_LOGIN_SALT``                       Specifies the salt value when
                                              generating login links/tokens.
                                              Defaults to ``login-salt``.
``SECURITY_REMEMBER_SALT``                    Specifies the salt value when
                                              generating remember tokens.
                                              Remember tokens are used instead
                                              of user ID's as it is more
                                              secure. Defaults to
                                              ``remember-salt``.
``SECURITY_DEFAULT_REMEMBER_ME``              Specifies the default "remember
                                              me" value used when logging in
                                              a user. Defaults to ``False``.
``SECURITY_DATETIME_FACTORY``                 Specifies the default datetime
                                              factory. Defaults to
                                              ``datetime.datetime.utcnow``.
============================================= ==================================

Messages
-------------

The following are the messages Flask-Security uses.  They are tuples; the first
element is the message and the second element is the error level.

The default messages and error levels can be found in ``core.py``.

* ``SECURITY_MSG_ALREADY_CONFIRMED``
* ``SECURITY_MSG_CONFIRMATION_EXPIRED``
* ``SECURITY_MSG_CONFIRMATION_REQUEST``
* ``SECURITY_MSG_CONFIRMATION_REQUIRED``
* ``SECURITY_MSG_CONFIRM_REGISTRATION``
* ``SECURITY_MSG_DISABLED_ACCOUNT``
* ``SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED``
* ``SECURITY_MSG_EMAIL_CONFIRMED``
* ``SECURITY_MSG_EMAIL_NOT_PROVIDED``
* ``SECURITY_MSG_FORGOT_PASSWORD``
* ``SECURITY_MSG_INVALID_CONFIRMATION_TOKEN``
* ``SECURITY_MSG_INVALID_EMAIL_ADDRESS``
* ``SECURITY_MSG_INVALID_LOGIN_TOKEN``
* ``SECURITY_MSG_INVALID_PASSWORD``
* ``SECURITY_MSG_INVALID_REDIRECT``
* ``SECURITY_MSG_INVALID_RESET_PASSWORD_TOKEN``
* ``SECURITY_MSG_LOGIN``
* ``SECURITY_MSG_LOGIN_EMAIL_SENT``
* ``SECURITY_MSG_LOGIN_EXPIRED``
* ``SECURITY_MSG_PASSWORDLESS_LOGIN_SUCCESSFUL``
* ``SECURITY_MSG_PASSWORD_CHANGE``
* ``SECURITY_MSG_PASSWORD_INVALID_LENGTH``
* ``SECURITY_MSG_PASSWORD_IS_THE_SAME``
* ``SECURITY_MSG_PASSWORD_MISMATCH``
* ``SECURITY_MSG_PASSWORD_NOT_PROVIDED``
* ``SECURITY_MSG_PASSWORD_NOT_SET``
* ``SECURITY_MSG_PASSWORD_RESET``
* ``SECURITY_MSG_PASSWORD_RESET_EXPIRED``
* ``SECURITY_MSG_PASSWORD_RESET_REQUEST``
* ``SECURITY_MSG_REFRESH``
* ``SECURITY_MSG_RETYPE_PASSWORD_MISMATCH``
* ``SECURITY_MSG_UNAUTHORIZED``
* ``SECURITY_MSG_USER_DOES_NOT_EXIST``

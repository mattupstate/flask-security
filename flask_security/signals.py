# -*- coding: utf-8 -*-
"""
    flask_security.signals
    ~~~~~~~~~~~~~~~~~~~~~~

    Flask-Security signals module

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

import blinker

signals = blinker.Namespace()

user_registered = signals.signal("user-registered")

user_confirmed = signals.signal("user-confirmed")

user_two_factored = signals.signal("user-two-factored")

confirm_instructions_sent = signals.signal("confirm-instructions-sent")

login_instructions_sent = signals.signal("login-instructions-sent")

password_reset = signals.signal("password-reset")

password_changed = signals.signal("password-changed")

two_factor_method_changed = signals.signal("two-factor-method-changed")

reset_password_instructions_sent = signals.signal(
    "password-reset-instructions-sent")

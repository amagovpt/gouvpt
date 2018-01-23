# -*- coding: utf-8 -*-
'''
Package for Authentication with portuguese Smart ID Cards
'''
from __future__ import unicode_literals

import logging

log = logging.getLogger(__name__)

def init_app(app):
    #Added Portuguese Single signOn with SmartCard
    from saml_govpt import autenticacao_gov
    from register_user import register_ptuser
    app.register_blueprint(autenticacao_gov)
    app.register_blueprint(register_ptuser)
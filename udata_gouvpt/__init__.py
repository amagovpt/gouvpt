# -*- coding: utf-8 -*-
'''
Package for Portuguese UData Plugins
'''
from __future__ import unicode_literals

import logging

log = logging.getLogger(__name__)

def init_app(app):
    #Added Portuguese Single signOn Plugin with PySAML2
    from saml_plugin.saml_govpt import autenticacao_gov
    from saml_plugin.register_user import register_ptuser
    app.register_blueprint(autenticacao_gov)
    app.register_blueprint(register_ptuser)


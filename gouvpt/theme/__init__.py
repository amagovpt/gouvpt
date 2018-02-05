# -*- coding: utf-8 -*-
'''
gouvpt

Official udata theme of the Open Data Portal of Portugal
'''
from __future__ import unicode_literals

import logging

from udata import theme
from udata.app import nav
from udata.i18n import lazy_gettext as _

log = logging.getLogger(__name__)


gouvpt_menu = nav.Bar('gouvpt_menu', [

    nav.Item(_('Open Data'), 'datasets.list', items=[
        nav.Item(_('Datasets'), 'datasets.list'),
        nav.Item(_('Reuses'), 'reuses.list'),
        nav.Item(_('Organizations'), 'organizations.list'),
        nav.Item(_('API'), 'apidoc.swaggerui'),
        nav.Item(_('Terms of use'), 'site.terms'),
    ]),
    nav.Item(_('Dashboard'), 'site.dashboard'),
    nav.Item(_('Blog/Events'), None, url='#', items=[
        nav.Item(_('Game of code'), None, url='http://www.gameofcode.eu/'),
    ]),
    nav.Item(_('Contact'), None, url='#'),
])

theme.menu(gouvpt_menu)

nav.Bar('gouvpt_footer', [
    nav.Item(_('API'), 'apidoc.swaggerui'),
    nav.Item(_('Terms of use'), 'site.terms'),
])

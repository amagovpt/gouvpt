# -*- coding: utf-8 -*-
'''
gouvpt

Official udata theme of the Open Data Portal of Portugal
'''
from __future__ import unicode_literals

import logging

from udata import theme
from udata.app import nav
from udata.core.post.models import Post
from udata.i18n import lazy_gettext as _

log = logging.getLogger(__name__)


gouvpt_menu = nav.Bar('gouvpt_menu', [

    nav.Item(_('Documentação'),  None, url='#', items=[
        nav.Item(_('Sobre dados abertos'), 'gouvpt.faq', {'section': 'about_opendata'}),
        nav.Item(_('Sobre o dados.gov'), 'gouvpt.faq', {'section': 'about_dadosgov'}),
        nav.Item(_('Publicar dados'), 'gouvpt.faq', {'section': 'publish'}),
        nav.Item(_('Reutilizar dados'), 'gouvpt.faq', {'section': 'reuse'}),
        nav.Item(_('Licenses'), 'gouvpt.faq', {'section': 'licenses'}),
        nav.Item(_('Acessibilidade'), 'gouvpt.faq', {'section': 'acessibilidade'}),
        nav.Item(_('API'), 'gouvpt.docapi'),
    ]),

    nav.Item(_('Dados Abertos'), None, url='#', items=[
        nav.Item(_('Datasets'), 'datasets.list'),
        #nav.Item(_('Data Analysis'), 'gouvpt.rawgraphs', {'embed': 'true'}),
        nav.Item(_('Reuses'), 'reuses.list'),
        nav.Item(_('Visualizações'), 'reuses.list', {'type': 'visualization'}),
        nav.Item(_('Organizations'), 'organizations.list'),
        nav.Item(_('Dashboard'), 'site.dashboard'),
        nav.Item(_('Map'), 'site.map'),
    ]),

    nav.Item(_('News'), None, url='#', items=[
        nav.Item(_('News'), 'posts.list'),
        nav.Item(_('Eventos'), 'posts.list', {'tag': 'evento'}),
    ]),

    nav.Item(_('Contact'), 'gouvpt.contact'),
])

theme.menu(gouvpt_menu)

@theme.context('home')
def home_context(context):
    context['banner_posts'] = Post.objects(tags='banner').published()
    context['featured_post'] = Post.objects(tags='destaque').published().first()
    return context
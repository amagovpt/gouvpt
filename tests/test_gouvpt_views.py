# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from flask import url_for

pytestmark = [
    pytest.mark.usefixtures('clean_db'),
    pytest.mark.options(THEME='gouvpt', PLUGINS=['gouvpt_saml', 'gouvpt_faqs']),
    pytest.mark.frontend,
]

EXTRA_PAGES = [
    ('gouvpt.credits', {}),
    ('gouvpt.contact', {}),
]

FAQ_SECTIONS = ('about_opendata', 'about_dadosgov', 'publish', 'reuse', 'licenses')

EXTRA_PAGES.extend([('gouvpt.faq', {'section': s}) for s in FAQ_SECTIONS])


@pytest.mark.parametrize('endpoint,kwargs', EXTRA_PAGES)
def test_render_view(client, endpoint, kwargs):
    '''It should render gouvpt views.'''
    assert client.get(url_for(endpoint, **kwargs)).status_code == 200

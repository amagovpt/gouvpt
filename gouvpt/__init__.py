# -*- coding: utf-8 -*-
'''
Official udata theme and extensions of the Open Data Portal of Portugal
'''
from __future__ import unicode_literals

__version__ = '0.1.0.dev'
__description__ = 'Official udata theme and extensions of the Open Data Portal of Portugal'

def init_app(app):
    from . import harvesters  # noqa: needed for registration
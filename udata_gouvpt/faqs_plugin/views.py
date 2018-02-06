# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata import theme
from udata.i18n import I18nBlueprint

blueprint = I18nBlueprint('gouvpt', __name__,
                          template_folder='../../gouvpt/theme/templates/custom',
                          static_folder='../../gouvpt/theme/static')

@blueprint.route('/credits/')
def credits():
    return theme.render('credits.html')
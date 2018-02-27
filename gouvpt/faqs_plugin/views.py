# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata import theme
from udata.i18n import I18nBlueprint
from flask import url_for, redirect, abort
from jinja2.exceptions import TemplateNotFound

blueprint = I18nBlueprint('gouvpt', __name__,
                          template_folder='../theme/templates/custom',
                          static_folder='../theme/static')


@blueprint.route('/faq/', defaults={'section': 'home'})
@blueprint.route('/faq/<string:section>/')
def faq(section):
    try:
        return theme.render('faq/{0}.html'.format(section), page_name=section)
    except TemplateNotFound:
        abort(404)

@blueprint.route('/credits/')
def credits():
    return theme.render('credits.html')
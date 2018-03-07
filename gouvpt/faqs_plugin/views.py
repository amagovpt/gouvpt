# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata import theme
from udata.i18n import I18nBlueprint
from flask import url_for, redirect, abort, Markup, render_template
from jinja2.exceptions import TemplateNotFound
import markdown, os, urllib2

blueprint = I18nBlueprint('gouvpt', __name__,
                          template_folder='../theme/templates/custom',
                          static_folder='../theme/static')


@blueprint.route('/faq/', defaults={'section': 'index'})
@blueprint.route('/faq/<string:section>/')
def faq(section):
    try:
        giturl = "https://raw.githubusercontent.com/amagovpt/docs.dados.gov.pt/master/faqs/{0}.md".format(section)
        response = urllib2.urlopen(giturl, timeout = 5).read().decode('utf8')
        content = Markup(markdown.markdown(response))
        return theme.render('faqs.html', page_name=section, content=content)
    except urllib2.URLError:
        abort(404)

@blueprint.route('/credits/')
def credits():
    return theme.render('credits.html')

@blueprint.route('/contact/')
def contact():
    return theme.render('contact.html')
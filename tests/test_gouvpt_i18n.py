# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import g, url_for
from werkzeug.routing import BuildError

from udata.i18n import I18nBlueprint, language

from udata.tests import DBTestMixin, WebTestMixin, TestCase
from udata.core.user.factories import UserFactory


bp = I18nBlueprint('i18nbp', __name__, static_folder='static')


@bp.route('/lang/<msg>/')
def lang(msg):
    return g.lang_code


@bp.route('/hardcoded/')
def hardcoded():
    out = g.lang_code + '-'
    with language('pt'):
        out += g.lang_code
    return out


@bp.route('/not-localized/', localize=False)
def not_localized():
    out = g.lang_code + '-'
    with language('pt'):
        out += g.lang_code
    return out


class I18nBlueprintTest(WebTestMixin, DBTestMixin, TestCase):
    def create_app(self):
        app = super(I18nBlueprintTest, self).create_app()
        app.config['DEFAULT_LANGUAGE'] = 'pt'
        app.config['LANGUAGES'] = {
            'en': 'English',
            'pt': 'Portuguese',
        }
        app.register_blueprint(bp)
        return app

    def test_lang_inserted_url_for(self):
        self.assertEqual(url_for('i18nbp.lang', msg='test'), '/pt/lang/test/')

    def test_redirect_url_for(self):
        self.assertEqual(
            url_for('i18nbp.lang_redirect', msg='test'), '/lang/test/')

    def test_lang_ignored_for_static(self):
        self.assertEqual(url_for('i18nbp.static', filename='test.jpg'),
                         '/static/test.jpg')
        with self.assertRaises(BuildError):
            url_for('i18nbp.static_redirect', filename='test.jpg')

    def test_redirect_on_missing_lang(self):
        response = self.get('/lang/test/?q=test')
        self.assertRedirects(response, '/pt/lang/test/?q=test')

    def test_do_not_redirect_and_set_lang(self):
        self.assertEqual(self.get('/pt/lang/test/').data, b'pt')
        self.assertEqual(self.get('/en/lang/test/').data, b'en')

    def test_redirect_on_default_lang_for_unknown_lang(self):
        self.assertRedirects(self.get('/sk/lang/test/'), '/pt/lang/test/')

    def test_404_on_default_lang_for_unknown_lang(self):
        self.assert404(self.get('/sk/not-found/'))

    def test_language_contact_manager(self):
        self.assertEqual(self.get('/pt/hardcoded/').data, b'pt-pt')
        self.assertEqual(self.get('/en/hardcoded/').data, b'en-pt')

    def test_redirect_user_prefered_lang(self):
        self.login(UserFactory(prefered_language='pt'))

        response = self.get('/lang/test/?q=test')
        self.assertRedirects(response, '/pt/lang/test/?q=test')

    def test_lang_ignored_for_localize_false(self):
        url = url_for('i18nbp.not_localized')
        self.assertEqual(url, '/not-localized/')

    def test_localized_url_redirect_for_localize_false(self):
        url = url_for('i18nbp.not_localized_redirect')
        self.assertEqual(url, '/pt/not-localized/')

        response = self.get(url)
        self.assertRedirects(response, '/not-localized/')

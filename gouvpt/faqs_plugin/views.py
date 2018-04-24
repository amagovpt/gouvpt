# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata import theme, mail, i18n
from udata.i18n import I18nBlueprint
from flask import url_for, redirect, abort, Markup, render_template, request, current_app
from jinja2.exceptions import TemplateNotFound
import markdown, urllib2

from flask_wtf import FlaskForm, recaptcha
from udata.forms import fields, validators
from flask_mail import Message
from flask_security.utils import do_flash

from udata.models import Dataset

class ContactForm(FlaskForm):
    name = fields.StringField("Name", [validators.Required()])
    email = fields.html5.EmailField("Email", [validators.Required(), validators.Email()])
    subject = fields.StringField("Subject", [validators.Required()])
    message = fields.TextAreaField("Message", [validators.Required()])
    recaptcha = recaptcha.RecaptchaField()

blueprint = I18nBlueprint('gouvpt', __name__,
                          template_folder='../theme/templates/custom',
                          static_folder='../theme/static')


#Dynamic FAQ's pages with local storage
@blueprint.route('/docs/', defaults={'section': 'index'})
@blueprint.route('/docs/<string:section>/')
def faq(section):
    try:
        giturl = "https://raw.githubusercontent.com/amagovpt/docs.dados.gov.pt/master/faqs/{0}.md".format(section)
        response = urllib2.urlopen(giturl, timeout = 2).read().decode('utf-8')
        content = Markup(markdown.markdown(response))
    except urllib2.URLError:
        try:
            with open('gouvpt/docs/{0}.md'.format(section), 'r') as f:
                response = f.read().decode('utf-8')
                content = Markup(markdown.markdown(response))
                return theme.render('faqs.html', page_name=section, content=content)
        except (IOError):
            abort(404)
    else:
        with open('gouvpt/docs/{0}.md'.format(section), 'w+') as f:
            f.write(response.encode('utf-8'))
        return theme.render('faqs.html', page_name=section, content=content)

#Credits page
@blueprint.route('/credits/')
def credits():
    return theme.render('credits.html')

#Contact Form page
@blueprint.route('/contact/', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate_on_submit() == False:
            for field, errors in form.errors.items():
                for error in errors:
                    do_flash(i18n.gettext(error),'danger')
        else:
            msg = Message(form.subject.data, sender=current_app.config.get('MAIL_DEFAULT_SENDER'), recipients=[current_app.config.get('MAIL_DEFAULT_RECEIVER')])
            msg.body = """
            From: %s <%s>
            %s
            """ % (form.name.data, form.email.data, form.message.data)
            try:
                mail = current_app.extensions.get('mail')
                mail.send(msg)
            except Exception, e:
                do_flash("Server Error : " + str(e), 'danger')
            else:
                do_flash(i18n.gettext(u"Thank you for your message. We'll get back to you shortly."), 'success')
    return theme.render('contact.html', form=form)

#Keep old API online
@blueprint.route('/v1/<string:org_slug>/<string:file_id>/', subdomain="servico")
def dadosGovOld_API(org_slug, file_id):
    format = 'json' if request.args.get('format') == 'json' else 'xml'
    dataset = Dataset.objects(__raw__={'extras.harvest:remote_id': file_id}).first()
    if dataset:
        for resource in dataset.resources:
            if resource.format == format:
                return redirect(resource.url)
    #Everything else return 404               
    return abort(404)
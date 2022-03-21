# -*- coding: utf-8 -*
#
##    Handle PasswordLess User Registration
##    

from flask import Blueprint, url_for, request, session, redirect

from flask_security.forms import Form
from flask_security.confirmable import send_confirmation_instructions
from flask_security.utils import get_message, do_flash
from flask_security.decorators import anonymous_user_required

from wtforms import ValidationError

from udata.forms import fields, validators
from udata.models import datastore
from udata import theme

from .saml_govpt import autenticacao_gov

def unique_user_email(form, field):
    if datastore.get_user(field.data) is not None:
        msg = get_message('EMAIL_ALREADY_ASSOCIATED', email=field.data)[0]
        raise ValidationError(msg)

class UserCustomForm(Form):
    email = fields.StringField(
        'Email Address', [validators.DataRequired('Email is required'), unique_user_email])
    first_name = fields.StringField(
        'First Name', [validators.DataRequired('First name is required')])
    last_name = fields.StringField(
        'Last Name', [validators.DataRequired('Last name is required')])
    user_nic = fields.HiddenField('NIC')


@autenticacao_gov.route('/saml/register', methods=['POST','GET'])
@anonymous_user_required
def register():
    form = UserCustomForm()
    #Create a new user
    if request.method == 'POST' and form.validate():
        data = {
            'first_name': str(request.values.get('first_name').encode('utf-8')).title(),
            'last_name': str(request.values.get('last_name').encode('utf-8')).title(),
            'email': str(request.values.get('email').encode('utf-8')),
        }

        if(request.values.get('user_nic')):
            data['extras'] = { 'auth_nic': str(request.values.get('user_nic')) }

        userUdata = datastore.create_user(**data)
        datastore.commit()
        send_confirmation_instructions(userUdata)
        do_flash(*get_message('CONFIRM_REGISTRATION', email=data['email']))
        return redirect(url_for('security.login'))
   
    else:
        form.email.data = session.get('user_email')
        if form.email.data:
            form.email.render_kw = {'readonly': True}
        form.first_name.data = session.get('first_name')
        form.last_name.data = session.get('last_name')
        form.user_nic.data = session.get('user_nic')
        return theme.render('security/register_saml.html', form = form)

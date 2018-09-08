# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from udata.i18n import lazy_gettext as _

from flask import current_app, render_template
from flask_mail import Message

from udata import theme
from udata.models import (
    Dataset, User, Role
)

log = logging.getLogger(__name__)

'''
Checks for missing datasets in source
'''
def missing_datasets_warning(job_items, source):

    job_datasets = [item.dataset.id for item in job_items]

    domain_harvested_datasets = Dataset.objects(__raw__={
        'extras.harvest:domain': source.domain
    }).all()
    
    missing_datasets = []
    for dataset in domain_harvested_datasets:
        if dataset.id not in job_datasets:
            missing_datasets.append(dataset)
    
    if missing_datasets:
        org_recipients = [ member.user.email for member in source.organization.members if member.role == 'admin' ]
        admin_role = Role.objects.filter(name='admin').first()
        recipients = [ user.email for user in User.objects.filter(roles=admin_role).all() ]

        recipients = list(set(org_recipients + recipients))

        subject = 'Dados.gov - Relatório de harvesting, {}.'.format(source)

        context = {
            'subject': subject,
            'harvester': source,
            'datasets': missing_datasets,
            'config': current_app.config
        }

        msg = Message(subject=subject, sender=current_app.config.get('MAIL_DEFAULT_SENDER'), recipients=recipients)
        msg.body = theme.render('mail/harvester_warning.txt', **context)
        msg.html = theme.render('mail/harvester_warning.html', **context)

        mail = current_app.extensions.get('mail')
        try:
            mail.send(msg)
        except:
            pass

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import uuid

from flask import current_app
from flask_mail import Message
from itertools import groupby

from udata import theme
from udata.models import Dataset, Role, User
from udata.tasks import job
from udata.utils import get_by

from udata.linkchecker.checker import check_resource

log = logging.getLogger(__name__)


@job('gouvpt_check_resources')
def check_resources(self, number=5000):
    '''Check <number> of URLs that have not been (recently) checked'''

    if not current_app.config.get('LINKCHECKING_ENABLED'):
        log.error('Link checking is disabled.')
        return

    base_pipeline = [
        {'$match': {'resources': {'$gt': []}}},
        {'$project': {'resources._id': True,
                      'resources.extras.check:date': True}},
        {'$unwind': '$resources'},
    ]
    # unchecked resources
    pipeline = base_pipeline + [
        {'$match': {'resources.extras.check:date': {'$eq': None}}},
        {'$limit': number}
    ]
    resources = list(Dataset.objects.aggregate(*pipeline))
    # not recently checked resources
    slots_left = number - len(resources)
    if slots_left:
        pipeline = base_pipeline + [
            {'$match': {'resources.extras.check:date': {'$ne': None}}},
            {'$sort': {'resources.extras.check:date': 1}},
            {'$limit': slots_left}
        ]
        resources += list(Dataset.objects.aggregate(*pipeline))

    nb_resources = len(resources)
    log.info('Checking %s resources...', nb_resources)

    resource_check_result = []
    for idx, dataset_resource in enumerate(resources):
        dataset_obj = Dataset.objects.get(id=dataset_resource['_id'])
        resource_id = dataset_resource['resources']['_id']
        rid = uuid.UUID(resource_id)
        resource_obj = get_by(dataset_obj.resources, 'id', rid)
        log.info('Checking resource %s (%s/%s)',
                 resource_id, idx + 1, nb_resources)
        if resource_obj.need_check():
            result = check_resource(resource_obj)
            #log.info(resource_obj.url)
            #log.info(result)
            if not result['check:available']:
                data = {
                    'dataset': dataset_obj,
                    'resource': resource_obj,
                    'status': result['check:status']
                }
                resource_check_result.append(data)
        else:
            log.info("--> Skipping this resource, cache is fresh enough.")

    #Group resources by dataset and send email
    if resource_check_result:
        resource_check_result.sort(key=lambda item: item['dataset'].id)
        resource_groups = groupby(resource_check_result, lambda item: item['dataset'])

        admin_role = Role.objects.filter(name='admin').first()
        recipients = [ user.email for user in User.objects.filter(roles=admin_role).all() ]

        subject = 'Relatório de verificação de links do dados.gov.'
        context = {
            'subject': subject,
            'resources': resource_groups,
            'server': current_app.config.get('SERVER_NAME')
        }

        msg = Message(subject=subject, sender='dados@ama.pt', recipients=recipients)
        #msg.body = theme.render('mail/link_checker_warning.txt', **context)
        msg.html = theme.render('mail/link_checker_warning.html', **context)

        mail = current_app.extensions.get('mail')
        try:
            mail.send(msg)
        except:
            pass

    log.info('Done.')

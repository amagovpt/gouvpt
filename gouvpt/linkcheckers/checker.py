# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import logging
import requests
from datetime import datetime
from flask import current_app

log = logging.getLogger(__name__)

# udata job schedule '0 7 * * 1'  gouvpt_check_resources
class Linkchecker(object):
    """ Gouvpt linkchecker """

    def check(self, resource):
        
        try:
            resp = requests.head(resource.url, timeout=5)
        except requests.exceptions.ConnectionError:
            code = 503
        except requests.exceptions.Timeout:
            code = 408
        else:
            code = resp.status_code

        return {
            'check:status': code,
            'check:available': code < 400,
            'check:date': datetime.now()
        }
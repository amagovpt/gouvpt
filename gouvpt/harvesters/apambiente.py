# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata.harvest.backends.base import BaseBackend
from udata.models import Resource, Dataset, License
from urllib import urlencode
from datetime import datetime
import requests
import urlparse

#backend = 'https://sniambgeoportal.apambiente.pt/geoportal/rest/find/document?max=5000&f=pjson'
class PortalAmbienteBackend(BaseBackend):
    display_name = 'Harvester Portal do Ambiente'

    def initialize(self):
        self.items = []
        r = requests.get(self.source.url).json()
        items = r['records']
        for item in items:
            try:
                item_datetime = datetime.strptime(item['updated'], "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
                
            try:
                dataset_lastdate = self.get_modifiedDate(item['id']).last_modified
            except AttributeError:
                self.add_item(item['id'], title=item['title'], date=item_datetime, item=item)
            else:
                if item_datetime > dataset_lastdate:
                    self.add_item(item['id'], title=item['title'], date=None, item=item)
                else:
                    continue

    def get_modifiedDate(self, remote_id):
        return Dataset.objects(__raw__={
            'extras.harvest:remote_id': remote_id,
            'extras.harvest:domain': self.source.domain
        }).first()

    def process(self, item):
        dataset = self.get_dataset(item.remote_id)
        # Here you comes your implementation. You should :
        # - fetch the remote dataset (if necessary)
        # - validate the fetched payload
        # - map its content to the dataset fields
        # - store extra significant data in the `extra` attribute
        # - map resources data

        kwargs = item.kwargs
        dataset.title = kwargs['title']
        dataset.license = License.guess('cc-by')
        dataset.tags = ["portal-ambiente"]
        item = kwargs['item']

        dataset.description = item['summary']

        if kwargs['date']:
            dataset.created_at = kwargs['date']

        # Force recreation of all resources
        dataset.resources = []
        for resource in item['links']:
            url = resource['href'].replace('\\','').replace (' ' ,'%20')
            type = resource['type']

            if type == 'details':
                dataset.description += "<br>"
                dataset.description += "<br>Mais detalhes : <a href=\"%s\" target=\"_blank\">%s</a>" % (url, dataset.title) 

            if type == 'open':
                url_parts = list(urlparse.urlparse(url))
                parts = url_parts[2].split('.')
                format = parts[-1] if len(parts)>1 else 'wms'
                new_resource = Resource(
                    title = dataset.title,
                    url = url,
                    filetype = 'remote',
                    format = format.lower()
                )
                dataset.resources.append(new_resource)

        return dataset

from udata.harvest.backends.base import BaseBackend
from udata.models import Resource, Dataset, License
import requests
from urllib.parse import urlparse
from datetime import datetime


#backend = 'https://snig.dgterritorio.gov.pt/rndg/srv/por/q?_content_type=json&fast=index&from=1&resultType=details&sortBy=referenceDateOrd&type=dataset%2Bor%2Bseries&dataPolicy=Dados%20abertos&keyword=DGT'
class DGTBackend(BaseBackend):
    display_name = 'Harvester DGT'

    def initialize(self):

        headers = {
            'content-type': 'application/json',
            'Accept-Charset': 'utf-8'
        }
        res = requests.get(self.source.url, headers=headers)
        res.encoding = 'utf-8'
        metadata = res.json().get("metadata")

        for each in metadata:
            item = {
                "remote_id": each.get("geonet:info", {}).get("uuid"),
                "title": each.get("defaultTitle"),
                "description": each.get("defaultAbstract"),
                "resources": each.get("link"),
                "keywords": each.get("keyword")
            }
            if each.get("publicationDate"):
                item["date"] = datetime.strptime(each.get("publicationDate"),
                                                 "%Y-%m-%d")

            links = []
            resources = item.get("resources")
            if isinstance(resources, list):
                for url in resources:
                    url_parts = url.split('|')
                    inner_link = {}
                    inner_link['url'] = url_parts[2]
                    inner_link['type'] = url_parts[3]
                    inner_link['format'] = url_parts[4]
                    links.append(inner_link)

            elif isinstance(resources, str):
                url_parts = resources.split('|')
                inner_link = {}
                inner_link['url'] = url_parts[2]
                inner_link['type'] = url_parts[3]
                inner_link['format'] = url_parts[4]
                links.append(inner_link)

            item['resources'] = links

            self.add_item(item["remote_id"], item=item)

    def process(self, item):
        dataset = self.get_dataset(item.remote_id)
        # Here you comes your implementation. You should :
        # - fetch the remote dataset (if necessary)
        # - validate the fetched payload
        # - map its content to the dataset fields
        # - store extra significant data in the `extra` attribute
        # - map resources data

        kwargs = item.kwargs
        item = kwargs['item']

        dataset.title = item['title']
        dataset.license = License.guess('cc-by')
        dataset.tags = ["snig.dgterritorio.gov.pt"]
        dataset.description = item['description']

        if item.get('date'):
            dataset.created_at = item['date']

        for keyword in item.get('keywords'):
            dataset.tags.append(keyword)

        # Force recreation of all resources
        dataset.resources = []

        for resource in item.get("resources"):

            parsed = urlparse.urlparse(resource['url'])
            try:
                format = str(urlparse.parse_qs(parsed.query)['service'][0])
            except KeyError:
                format = resource['url'].split('.')[-1]

            new_resource = Resource(title=item['title'],
                                    url=resource['url'],
                                    filetype='remote',
                                    format=format)

            dataset.resources.append(new_resource)

        dataset.extras['harvest:name'] = self.source.name

        return dataset

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata.harvest.backends.base import BaseBackend
from udata.models import Resource, Dataset, License
import requests, urlparse
from bs4 import BeautifulSoup
from datetime import datetime

payload = """
<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" xmlns:apiso="http://www.opengis.net/cat/csw/apiso/1.0" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gmd="http://www.isotc211.org/2005/gmd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" service="CSW" version="2.0.2" maxRecords="100" startPosition="1" resultType="results" outputFormat="application/xml" outputSchema="http://www.isotc211.org/2005/gmd" xsi:schemaLocation="http://www.opengis.net/cat/csw/2.0.2                        http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd">
  <csw:Query typeNames="gmd:MD_Metadata">  
      <csw:ElementSetName typeNames="gmd:MD_Metadata">full</csw:ElementSetName>
      <csw:Constraint version="1.1.0">
         <ogc:Filter>
		 <ogc:And>
		 <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>apiso:Type</ogc:PropertyName>
                  <ogc:Literal>service</ogc:Literal>
               </ogc:PropertyIsEqualTo>
			<ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>Subject</ogc:PropertyName>
                  <ogc:Literal>iGEO</ogc:Literal>
               </ogc:PropertyIsEqualTo>
			    <ogc:PropertyIsLike>
                  <ogc:PropertyName>Subject</ogc:PropertyName>
                  <ogc:Literal>DGT</ogc:Literal>
               </ogc:PropertyIsLike>
			 </ogc:And>
            </ogc:Filter>
      </csw:Constraint>
   </csw:Query> 
</csw:GetRecords>
"""

#backend = 'http://snig.dgterritorio.pt/geoportal/csw/discovery'
class DGTBackend(BaseBackend):
    display_name = 'Harvester DGT'

    def initialize(self):
        self.items = []
        headers = {'content-type': 'text/xml', 'Accept-Charset': 'UTF-8'}
        r = requests.post(self.source.url, data=payload, headers=headers)
        soup = BeautifulSoup(r.text, 'xml')

        for item in soup.find_all('gmd:MD_Metadata'):
            remote_id = item.find('gmd:fileIdentifier').text.replace('\n', '')
            date = item.find('gmd:dateStamp').text.replace('\n', '')
            dataset_info = item.find('gmd:identificationInfo')
            title = dataset_info.find('gmd:title').text.replace('\n', '')
            description = dataset_info.find('gmd:abstract').text.replace('\n', '')
            keyword_info = dataset_info.find('gmd:descriptiveKeywords')
            keywords = [key.text.replace('\n', '') for key in keyword_info.find_all('gmd:keyword')]
            resources = [link.text.replace('\n', '') for link in item.find_all('gmd:CI_OnlineResource')][-1]

            item = {
                "remote_id": remote_id,
                "title": title,
                "date": datetime.strptime(date, "%Y-%m-%d"),
                "description": description,
                "resources": resources,
                "keywords": keywords
            }

            self.add_item(remote_id, item=item)

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
        dataset.tags = ["snig.dgterritorio.pt"]
        dataset.description = item['description']

        if item['date']:
            dataset.created_at = item['date']

        for keyword in item['keywords']:
            dataset.tags.append(keyword)

        # Force recreation of all resources
        dataset.resources = []

        parsed = urlparse.urlparse(item['resources'])
        try:
            format = str(urlparse.parse_qs(parsed.query)['service'][0])
        except KeyError:
            format = 'wms'

        new_resource = Resource(
            title = dataset.title,
            url = str(item['resources']),
            filetype = 'remote',
            format = format
        )

        dataset.resources.append(new_resource)

        dataset.extras['harvest:name'] = self.source.name

        return dataset

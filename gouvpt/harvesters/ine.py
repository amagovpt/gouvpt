from udata.models import db, Resource, License

from udata.harvest.backends.base import BaseBackend

from datetime import datetime
from xml.dom import minidom, Node
import requests


class INEBackend(BaseBackend):
    display_name = 'Instituto nacional de estatística'

    def initialize(self):
        try:
            from ineDatasets import datasetIds
        except :
            datasetIds = set([])

        req = requests.get(self.source.url)
        doc = minidom.parseString(req.content)

        properties = doc.getElementsByTagName('indicator')

        for propNode in properties:
            currentId = propNode.attributes['id'].value
            datasetIds.add(currentId)

        for dsId in datasetIds:
            self.add_item(dsId)

    def process(self, item):
        '''Return the INE datasets'''

        dataset = self.get_dataset(item.remote_id)

       # get remote data for dataset
        req = requests.get(
            "https://www.ine.pt/ine/xml_indic.jsp"
            , params={ 
                'varcd': item.remote_id
                , 'lang': 'PT' 
                , 'opc': '1' 
            }
            , headers={'charset': 'utf8'}
        )

        returnedData = req.content
        print('Get metadata for %s' % (item.remote_id))

        keywordSet = set()
        dataset.license = License.guess('cc-by')
        dataset.resources = []
        doc = minidom.parseString(returnedData)
        properties = doc.getElementsByTagName('indicator')
        # go through the API dataset information
        for propNode in properties:
            for childNode in propNode.childNodes:
                # print childNode
                fc = childNode.firstChild
                if fc:
                    if childNode.nodeName == 'keywords':
                        for obj in childNode.childNodes:
                            # INE needs to create a proper xml file...
                            valueData = obj.nodeValue
                            # need to ignore the ',' nodes
                            if obj.nodeValue != ',':
                                # need to ignore the last "," usually after the INE value
                                if valueData[-1:] == ',':
                                    valueData = valueData[:-1]
                                # this removes redundant keywords that sometimes show with different cases (lower and upper)
                                keywordSet.add(valueData.lower())

                        dataset.tags = list(keywordSet)
                        dataset.tags.append('ine.pt')
                        dataset.frequency = 'unknown'

                    elif childNode.nodeName == 'title':
                        dataset.title = fc.nodeValue

                    elif childNode.nodeName == 'description':
                        dataset.description = fc.nodeValue

                    elif childNode.nodeName == 'html':
                        for obj in childNode.childNodes:
                            if obj.nodeName == 'bdd_url':
                                dataset.description += "\n " + obj.firstChild.nodeValue

                    elif childNode.nodeName == 'json':
                        for obj in childNode.childNodes:
                            if obj.nodeName == 'json_dataset':
                                dataset.resources.append(Resource(
                                    title = 'Dataset json url'
                                    , description = 'Dataset em formato json'
                                    , url = obj.firstChild.nodeValue
                                    , filetype='remote'
                                    , format = 'json'
                                ))
                            elif obj.nodeName == 'json_metainfo':
                                dataset.resources.append(Resource(
                                    title = 'Json metainfo url'
                                    , description = 'Metainfo em formato json'
                                    , url = obj.firstChild.nodeValue
                                    , filetype='remote'
                                    , format = 'json'
                                ))
        return dataset
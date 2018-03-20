# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata.models import db, Resource
from udata.utils import faker

from udata.harvest.backends.base import BaseBackend
from udata.core.organization.models import Organization

from flask import url_for

from xml.dom import minidom, Node
import urllib2
import urllib
import requests
import csv
import sys
import os
import errno
import json
import traceback


class INEBackend(BaseBackend):
    display_name = 'Instituto nacional de estatística'

    def initialize(self):
        '''Get the datasets and corresponding organization ids'''

        try:
            from ineDatasets import datasetIds
        except :
            datasetIds = set([])

        print '-------------------------------------'
        print 'using url %s' % self.source.url
        req = requests.get(self.source.url)
        doc = minidom.parseString(req.content)

        properties = doc.getElementsByTagName('indicator')
        # go through the API dataset information
        for propNode in properties:
            currentId = propNode.attributes['id'].value
            datasetIds.add(currentId)

        numberSets = 0
        # **************************************
        # common code starts here
        for dsId in datasetIds:
            self.add_item(
                dsId
            )
            numberSets += 1
        # **************************************
        print '-------------------------------------'
        print 'Total sets => %s' % numberSets
        print '-------------------------------------'

    def process(self, item):
        '''Return the INE datasets'''

        # **************************************
        # ugly fix for encoding problems
        reload(sys)
        sys.setdefaultencoding('utf8')
        # **************************************

         # Get or create a harvested dataset with this identifier.
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
        print 'Get metadata for %s' % (item.remote_id)

        keywordSet = set()
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

                    elif childNode.nodeName == 'title':
                        dataset.title = fc.nodeValue

                    elif childNode.nodeName == 'description':
                        dataset.description = fc.nodeValue

                    elif childNode.nodeName == 'html':
                        for obj in childNode.childNodes:
                            if obj.nodeName == 'bdd_url':
                                dataset.resources.append(Resource(
                                    title = 'Dataset html url'
                                    , description = 'Dataset em formato user friendly'
                                    , url = obj.firstChild.nodeValue
                                    , filetype='remote'
                                    , format = 'xml'
                                ))
                            elif obj.nodeName == 'metainfo_url':
                                dataset.resources.append(Resource(
                                    title = 'Dataset metainfo url'
                                    , description = 'Metainfo em formato user friendly'
                                    , url = obj.firstChild.nodeValue
                                    , filetype='remote'
                                    , format = 'xml'
                                ))

                    elif childNode.nodeName == 'json':
                        for obj in childNode.childNodes:
                            if obj.nodeName == 'json_dataset':
                                dataset.resources.append(Resource(
                                    title = 'Dataset json url'
                                    , description = 'Dataset em formato json'
                                    , url = obj.firstChild.nodeValue
                                    , filetype='remote'
                                    , format = 'xml'
                                ))
                            elif obj.nodeName == 'json_metainfo':
                                dataset.resources.append(Resource(
                                    title = 'Json metainfo url'
                                    , description = 'Metainfo em formato json'
                                    , url = obj.firstChild.nodeValue
                                    , filetype='remote'
                                    , format = 'xml'
                                ))

        # unused
        # dataset.organization = orgObj.id
        # dataset.created_at = item.kwargs['createdOn']
        # dataset.extras = {}
        # dataset.extras['contact'] = fc.nodeValue
        # dataset.extras['links'] = '%s, %s' % (dataset.extras['links'], fc.nodeValue)
        return dataset
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

sys.path.append('/home/udata')
from ftpCreds import ftpCredsObj

REPORT_FILE_PATH = '/home/udata/report.csv'
dadosGovPath = 'dadosGovFiles'
downloadFilePath = '/home/udata/fs/%s' % (dadosGovPath)

class DGBackend(BaseBackend):
    display_name = 'Dados Gov'

    def initialize(self):
        '''Get the datasets and corresponding organization ids'''
        global REPORT_FILE_PATH, downloadFilePath

        print '------------------------------------'
        print 'Initializing dados gov harvester'
        print '------------------------------------'

        with open(REPORT_FILE_PATH, 'wb') as csvResFile:
            writer = csv.writer(csvResFile, delimiter=chr(9), quotechar=chr(34), quoting=csv.QUOTE_MINIMAL)
            writer.writerow([
                'DatasetId'
                , 'DatasetName'
                , 'Organization'
                , 'Tags'
                , 'FileOriginal'
                , 'FileXML'
                , 'Topic'
                , 'TagsAdicionarDataset'
            ])

        auxFilePath = '/home/udata'
        # ******************************************************************************
        # store the data regarding organizations that matter from the db exported file
        organizationData = {}
        with open('%s/organizations.csv' % auxFilePath) as f:
            reader = csv.reader(f, delimiter=chr(9))

            for row in reader:
                # ignore this organization
                if row[6] == 'portaldosnsareadatransparencia':
                    continue

                # 1, 2, 6 => name, description, acronym, slug
                organizationData[row[6]] = { 'name': row[1], 'description': row[2], 'acronym': row[6] }
        # ******************************************************************************


        # ******************************************************************************
        # get dataset original filePath in a dictionary
        datasetDbFileData = {}
        with open("%s/datasetByName.csv" % auxFilePath) as f:
            reader = csv.reader(f, delimiter=chr(9))

            for row in reader:
                # if theres no filePath insert empty string
                if not row[12]:
                    row[12] = ''

                # if theres no service url insert empty string
                if not row[3]:
                    row[3] = ''

                datasetDbFileData[row[1]] = {
                    'filePath': row[12][14:]
                    , 'serviceUrl': row[3]
                    , 'createdOn': row[9]
                }
        # ******************************************************************************


        # ******************************************************************************
        # associate api datasets and organizations with its organization
        rootUrl = "http://servico.dados.gov.pt/v1/"
        xmlRootData = urllib2.urlopen(rootUrl).read()
        organizationDoc = minidom.parseString(xmlRootData)
        organizationElements = organizationDoc.getElementsByTagName('collection')

        for orgElement in organizationElements:
            orgName = orgElement.attributes['href'].value
            datasetUrl = "http://servico.dados.gov.pt/v1/%s" % orgName
            xmlDatasetData = urllib2.urlopen(datasetUrl).read()
            datasetDoc = minidom.parseString(xmlDatasetData)
            datasetElements = datasetDoc.getElementsByTagName('collection')

            # associate the current dataset with the previously added db data
            if orgName in organizationData:
                orgData = organizationData[orgName]
            else:
                orgData = { 'name': orgName, 'description': orgName, 'acronym': orgName }


            print '------------------------------------'
            print 'Adding datasets for organization "%s"' % orgName
            # if there are any elements in the organization
            if datasetElements:
                # check if the current organization exists in the db, if not create it
                orgObj = Organization.objects(acronym=orgData['acronym']).first()

                if not orgObj:
                    print '--'
                    orgObj = Organization()
                    orgObj.acronym = orgData['acronym']
                    print 'Created %s' % orgObj.acronym
                    print '--'

                orgObj.name = orgData['name']
                orgObj.description = orgData['description']
                orgObj.save()

                orgData['dbOrgId'] = orgObj.id

                for dsElement in datasetElements:
                    datasetName = dsElement.attributes['href'].value

                    if datasetName in datasetDbFileData:
                        self.add_item(
                            datasetName
                            , orgId = orgObj.id
                            , orgAcronym = orgObj.acronym
                            , filePath = datasetDbFileData[datasetName]['filePath']
                            , serviceUrl = datasetDbFileData[datasetName]['serviceUrl']
                            , createdOn = datasetDbFileData[datasetName]['createdOn']
                        )

                        # print 'Added dataset "%s"' % datasetName

        if not os.path.exists(downloadFilePath):
            try:
                os.makedirs(downloadFilePath)
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        # ******************************************************************************

    def process(self, item):
        '''Return the DadosGov datasets with the corresponding original and xml file'''
        global REPORT_FILE_PATH, ftpCredsObj, dadosGovPath, downloadFilePath

        # Get or create a harvested dataset with this identifier.
        dataset = self.get_dataset(item.remote_id)
        # get the organization object, no check necessary, it should always exist
        orgObj = Organization.objects(id=item.kwargs['orgId']).first()

        print '------------------------------------'
        print 'Processing %s (%s)' % (dataset.title, item.remote_id)
        # print item.kwargs
        # print '--'

        # set additional vars
        dataset.tags = ['migrado']
        dataset.extras = {}
        dataset.organization = orgObj.id
        dataset.resources = []
        
        # print item.kwargs['orgId']
        # *********************************************
        # go through the DB dataset information
        dataset.created_at = item.kwargs['createdOn']
        dataset.extras['links'] = item.kwargs['serviceUrl']
        # ********************************************************

        # ********************************************************
        # API metadata(nameexternal, description, contact, category, links, keywords):
        # http://servico.dados.gov.pt/v1/dgal/TableMetadata/?$filter=partitionkey%20eq%20%27AIIIDM2013%27
        # rootUrl = "http://servico.dados.gov.pt/v1/%s/TableMetadata/?$filter=partitionkey eq '%s'" % (item.kwargs['orgAcronym'], item.remote_id)
        # rootUrl = 'http://servico.dados.gov.pt/v1/%s/TableMetadata/?$filter=partitionkey%20eq%20%27%s%27' % (item.kwargs['orgAcronym'], item.remote_id)
        # rootUrl = 'http://servico.dados.gov.pt/v1/%s/TableMetadata/?$filter=partitionkey%20eq%20%27' + item.remote_id + '%27' % (item.kwargs['orgAcronym'])


        # xmlRootData = urllib2.urlopen(rootUrl).read()
        req = requests.get(
            "http://servico.dados.gov.pt/v1/%s/TableMetadata" % item.kwargs['orgAcronym']
            , params={ '$filter': "partitionkey eq '%s'" % item.remote_id }
            , headers={'charset': 'utf8'})

        # print req.url
        # print '--'
        xmlRootData = req.content

        propertiesDoc = minidom.parseString(xmlRootData)
        propertiesStuff = propertiesDoc.getElementsByTagName('content')
        propEl = propertiesDoc.getElementsByTagNameNS('*', 'properties')
        if propEl:
            propertiesElements = propEl[0].childNodes

            # go through the API dataset information
            for propEl in propertiesElements:
                if propEl.nodeType == Node.ELEMENT_NODE:
                    fc = propEl.firstChild

                    if fc:
                        if propEl.nodeName == 'd:category':
                            dataset.tags.append(fc.nodeValue)

                        elif propEl.nodeName == 'd:keywords':
                            dataset.tags.extend([currentTag.strip() for currentTag in fc.nodeValue.split(',')])

                        # elif propEl.nodeName == 'd:PartitionKey':
                        #     dataset.slug = fc.nodeValue

                        elif propEl.nodeName == 'd:nameexternal':
                            dataset.title = fc.nodeValue

                        elif propEl.nodeName == 'd:description':
                            dataset.description = fc.nodeValue

                        elif propEl.nodeName == 'd:contact':
                            dataset.extras['contact'] = fc.nodeValue

                        elif propEl.nodeName == 'd:links' and fc.nodeValue:
                            dataset.extras['links'] = '%s, %s' % (dataset.extras['links'], fc.nodeValue)
            # ********************************************************

            reload(sys)
            sys.setdefaultencoding('utf8')

            fixedUrl = url_for(
                'site.home'
                , _external=True
            )
            fixedUrl = '%s/s/%s' % (fixedUrl[: fixedUrl.rfind('/', 0, -1)], dadosGovPath)
            # empty previous dataset resources
            dataset.resources = []

            # separate filename from extension
            filename = os.path.splitext(item.kwargs['filePath'])

            # ********************************************************
            # get xml by api and set the dataset resource field:
            # http://servico.dados.gov.pt/v1/dgal/AIIIDM2013
            # print '----------------------'
            # print filename

            filenameXml = '%s.xml' % (filename[0])
            # filenameXml = '%s.xml' % (item.remote_id)
            u = urllib2.urlopen("http://servico.dados.gov.pt/v1/%s/%s" % (item.kwargs['orgAcronym'], item.remote_id))

            # create/open the local file to be written
            with open('%s/%s' % (downloadFilePath, filenameXml), 'wb') as f:
                # write file data
                f.write(u.read())

                # get file size info
                meta = u.info()
                fileSize = int(meta.getheaders("Content-Length")[0])
                urlSafe = urllib.quote(filename[0])
                fullPath = '%s/%s.xml' % (fixedUrl, urlSafe)
                print fullPath

                # set the resource data for the dataset
                dataset.resources.append(Resource(
                    title = dataset.title
                    , description = 'Dados em formato xml'
                    # , url = '/s/%s/%s' % (dadosGovPath, filenameXml)
                    # http://localhost/s/resources/aiiidm2010-8/20180226-215249/NomeCompleto.png
                    # , url = 'http://google.com'
                    , url = fullPath
                    # this is the default
                    # , filetype = 'file'
                    , mime = 'text/xml '
                    , format = 'xml'
                    , filesize = fileSize
                    , created_at = item.kwargs['createdOn']
                ))
            # ********************************************************

            # ********************************************************
            # get original files using static path and ftp and set the dataset resource field

            if item.kwargs['filePath']:
                try:
                    # https://dadosgovstorage.blob.core.windows.net/datasetsfiles/Acesso%20a%20Consultas%20M%C3%A9dicas%20pela%20Popula%C3%A7%C3%A3o%20Inscrita_636046701023924396.xlsx
                    urlSafe = urllib.quote(item.kwargs['filePath'])
                    print "https://dadosgovstorage.blob.core.windows.net/datasetsfiles/%s" % (urlSafe)
                    u = urllib2.urlopen("https://dadosgovstorage.blob.core.windows.net/datasetsfiles/%s" % (urlSafe))

                    # create/open the local file to be written
                    with open('%s/%s' % (downloadFilePath, item.kwargs['filePath']), 'wb') as f:
                        # write file data
                        f.write(u.read())

                        # get file size info
                        meta = u.info()
                        fileSize = int(meta.getheaders("Content-Length")[0])
                        fullPath = '%s/%s' % (fixedUrl, urlSafe)
                        print fullPath

                        # set the resource data for the dataset
                        dataset.resources.append(Resource(
                            title = dataset.title
                            , description = 'Ficheiro original'
                            # http://localhost/s/resources/aiiidm2010-8/20180226-215249/NomeCompleto.png
                            , url = fullPath
                            # this is the default
                            # , filetype = 'file'
                            , mime = 'application/vnd.ms-excel'
                            , format = filename[1][1:]
                            , filesize = fileSize
                            , created_at = item.kwargs['createdOn']
                        ))

                # file not found exception
                except IOError as ex:
                    print 'Original file not found:'
                    print ex
            
            # import paramiko
            # with paramiko.Transport((ftpCredsObj['host'], ftpCredsObj['port'])) as transport:
            #     transport.connect(username = ftpCredsObj['username'], password = ftpCredsObj['password'])

            #     with paramiko.SFTPClient.from_transport(transport) as sftp:
            #         if item.kwargs['filePath']:
            #             try:
            #                 # get file information
            #                 fileAttributes = sftp.stat('/%s' % item.kwargs['filePath'])

            #                 # download the original file
            #                 fullPath = '%s/%s%s' % (fixedUrl, item.remote_id, filename[1])
            #                 sftp.get('/%s' % item.kwargs['filePath'], '%s/%s%s' % (downloadFilePath, item.remote_id, filename[1]))
            #                 print fullPath

            #                 # set the resource data for the dataset
            #                 dataset.resources.append(Resource(
            #                     title = dataset.title
            #                     , description = 'Ficheiro original (%s)' % (item.kwargs['filePath'])
            #                     # , url = 'http://google.com'
            #                     # , url = '%s/%s' % (fixedUrl, item.kwargs['filePath'])
            #                     , url = fullPath
            #                     , filetype = 'file'
            #                     , mime = 'application/vnd.ms-excel'
            #                     , format = filename[1][1:]
            #                     , filesize = fileAttributes.st_size
            #                     , created_at = item.kwargs['createdOn']
            #                 ))

            #             # file not found exception
            #             except IOError as ex:
            #                 print 'Original file not found:'
            #                 print ex

            # ********************************************************

            print '--'
            print 'Returning %s' % dataset.title
            print '------------------------------------'
            with open(REPORT_FILE_PATH, 'a') as csvResFile:
                writer = csv.writer(csvResFile, delimiter=chr(9), quotechar=chr(34), quoting=csv.QUOTE_MINIMAL)
                writer.writerow([
                    item.remote_id
                    , dataset.title
                    , orgObj.name
                    , json.dumps(dataset.tags, ensure_ascii=False)
                    , item.kwargs['filePath']
                    , filenameXml
                    , ''
                    , '[]'
                ])

            # update the number of datasets associated with this organization
            orgObj.metrics['datasets'] += 1
            orgObj.save()

            return dataset

        print 'No data returned from the API for the dataset %s' % (item.remote_id)
        with open(REPORT_FILE_PATH, 'a') as csvResFile:
            writer = csv.writer(csvResFile, delimiter=chr(9), quotechar=chr(34), quoting=csv.QUOTE_MINIMAL)
            writer.writerow([
                item.remote_id
                , ''
                , ''
                , ''
                , item.kwargs['filePath']
                , ''
                , ''
                , '[]'
            ])

        return None
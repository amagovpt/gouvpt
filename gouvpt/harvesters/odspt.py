# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from mimetypes import guess_extension

import html2text
from dateutil.parser import parse as parse_date

from flask import url_for

from udata.i18n import lazy_gettext as _
from udata.harvest.backends.base import BaseBackend
from udata.harvest.exceptions import HarvestSkipException
from udata.models import License, Resource, Organization
from udata.utils import get_by

from urlparse import urlparse


class OdsBackendPT(BaseBackend):
    display_name = 'OpenDataSoft PT'
    verify_ssl = False

    # above this records count limit, shapefile export will be disabled
    # since it would be a partial export
    SHAPEFILE_RECORDS_LIMIT = 50000

    LICENSES = {
        'Open Database License (ODbL)': 'odc-odbl',
        'Licence Ouverte (Etalab)': 'fr-lo',
        'Licence ouverte / Open Licence': 'fr-lo',
        'CC BY-SA': 'cc-by-sa',
        'Public Domain': 'other-pd'
    }

    FORMATS = {
        'csv': ('CSV', 'csv', 'text/csv'),
        'geojson': ('GeoJSON', 'json', 'application/vnd.geo+json'),
        'json': ('JSON', 'json', 'application/json'),
        'shp': ('Shapefile', 'shp', None),
    }

    @property
    def source_url(self):
        return self.source.url.rstrip('/')

    @property
    def api_url(self):
        return '{0}/api/datasets/1.0/search/'.format(self.source_url)

    def explore_url(self, dataset_id):
        return '{0}/explore/dataset/{1}/'.format(self.source_url, dataset_id)

    def alternative_export_url(self, dataset_id, export_id):
        return '{0}/api/datasets/1.0/{1}/alternative_exports/{2}'.format(
            self.source_url, dataset_id, export_id)

    def download_url(self, dataset_id, format):
        return ('{0}download?format={1}&timezone=Europe/Berlin'
                '&use_labels_for_header=true'
                ).format(self.explore_url(dataset_id), format)

    def export_url(self, dataset_id):
        return '{0}?tab=export'.format(self.explore_url(dataset_id))

    def initialize(self):
        count = 0
        nhits = None

        def should_fetch():
            if nhits is None:
                return True
            max_value = min(nhits, self.max_items) if self.max_items else nhits
            return count < max_value

        while should_fetch():
            response = self.get(self.api_url, params={
                'start': count,
                'rows': 50,
                'interopmetas': 'true',
            })
            response.raise_for_status()
            data = response.json()
            nhits = data['nhits']
            for dataset in data['datasets']:
                count += 1
                self.add_item(dataset['datasetid'], dataset=dataset)

    def process(self, item):
        ods_dataset = item.kwargs['dataset']
        dataset_id = ods_dataset['datasetid']
        ods_metadata = ods_dataset['metas']
        ods_interopmetas = ods_dataset.get('interop_metas', {})

        if not ods_dataset.get('has_records'):
            msg = 'Dataset {datasetid} has no record'.format(**ods_dataset)
            raise HarvestSkipException(msg)

        # TODO: This behavior should be enabled with an option
        if 'inspire' in ods_interopmetas:
            msg = 'Dataset {datasetid} has INSPIRE metadata'
            raise HarvestSkipException(msg.format(**ods_dataset))

        dataset = self.get_dataset(item.remote_id)

        dataset.title = ods_metadata['title']
        dataset.frequency = 'unknown'
        description = ods_metadata.get('description', '').strip()
        description = html2text.html2text(description.strip('\n').strip(),
                                          bodywidth=0)
        dataset.description = description.strip().strip('\n').strip()
        dataset.private = False

        # Detect Organization
        try:
            organization_acronym = ods_metadata['publisher']
        except KeyError:
            pass
        else:
            orgObj = Organization.objects(acronym=organization_acronym).first()
            if orgObj:
                print 'Found %s' % orgObj.acronym
                dataset.organization = orgObj.id
            else:
                orgObj = Organization()
                orgObj.acronym = organization_acronym
                orgObj.name = organization_acronym
                orgObj.description = organization_acronym
                orgObj.save()
                print 'Created %s' % orgObj.acronym

                dataset.organization = orgObj.id

        
        tags = set()
        if 'keyword' in ods_metadata:
            if isinstance(ods_metadata['keyword'], list):
                tags |= set(ods_metadata['keyword'])
            else:
                tags.add(ods_metadata['keyword'])

        if 'theme' in ods_metadata:
            if isinstance(ods_metadata['theme'], list):
                for theme in ods_metadata['theme']:
                    tags.update([t.strip().lower() for t in theme.split(',')])
            else:
                themes = ods_metadata['theme'].split(',')
                tags.update([t.strip().lower() for t in themes])

        dataset.tags = list(tags)
        dataset.tags.append(urlparse(self.source.url).hostname)

        # Detect license
        default_license = dataset.license or License.default()
        license_id = ods_metadata.get('license')
        dataset.license = License.guess(license_id,
                                        self.LICENSES.get(license_id),
                                        default=default_license)

        self.process_resources(dataset, ods_dataset, ('csv', 'json'))

        if 'geo' in ods_dataset['features']:
            exports = ['geojson']
            if ods_metadata['records_count'] <= self.SHAPEFILE_RECORDS_LIMIT:
                exports.append('shp')
            self.process_resources(dataset, ods_dataset, exports)

        if 'alternative_exports' in ods_dataset:
            self.process_alternative_exports(dataset, ods_dataset)

        dataset.extras['ods:url'] = self.explore_url(dataset_id)
        if 'references' in ods_metadata:
            dataset.extras['ods:references'] = ods_metadata['references']
        dataset.extras['ods:has_records'] = ods_dataset['has_records']
        dataset.extras['ods:geo'] = 'geo' in ods_dataset['features']

        return dataset

    def process_alternative_exports(self, dataset, data):
        dataset_id = data['datasetid']
        modified_at = self.parse_date(data['metas']['modified'])
        for export in data['alternative_exports']:
            url = self.alternative_export_url(dataset_id, export['id'])
            created, resource = self.get_resource(dataset, url)
            resource.title = export.get('title', 'No title')
            if 'description' in export:
                resource.description = export['description']
            if 'mimetype' in export:
                resource.mime = export['mimetype']
                resource.format = self.guess_format(export['mimetype'])
            resource.modified = modified_at
            if created:
                dataset.resources.append(resource)

    def get_resource(self, dataset, url):
        resource = get_by(dataset.resources, 'url', url)
        if not resource:
            return True, Resource(url=url)
        return False, resource

    def process_resources(self, dataset, data, formats):
        dataset_id = data['datasetid']
        ods_metadata = data['metas']
        modified_at = self.parse_date(ods_metadata['modified'])
        description = self.description_from_fields(data['fields'])
        for _format in formats:
            label, udata_format, mime = self.FORMATS[_format]
            url = self.download_url(dataset_id, _format)
            created, resource = self.get_resource(dataset, url)
            resource.title = _('Export to {format}').format(format=label)
            resource.description = description
            resource.filetype = 'remote'
            resource.format = udata_format
            resource.mime = mime
            resource.modified = modified_at
            if hasattr(resource, 'preview_url'):
                # Add preview with backward compatibility
                resource.preview_url = url_for('ods.preview',
                                               domain=self.source.domain,
                                               id=dataset_id,
                                               _external=True,
                                               _scheme='')
            if created:
                dataset.resources.append(resource)

    def description_from_fields(self, fields):
        '''Build a resource description/schema from ODS API fields'''
        if not fields:
            return

        out = ''
        for field in fields:
            out += '- *{label}*: {name}[{type}]'.format(**field)
            if field.get('description'):
                out += ' {description}'.format(**field)
            out += '\n'
        return out

    def parse_date(self, date_str):
        try:
            return parse_date(date_str)
        except ValueError:
            pass

    def guess_format(self, mimetype):
        ext = guess_extension(mimetype)
        if ext:
            ext = ext.replace('.', '')
        return ext
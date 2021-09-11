import mimetypes
import os

from dateutil.parser import parse as parse_date

from udata.frontend.markdown import parse_html
from udata.i18n import gettext as _
from udata.harvest.backends.base import BaseBackend, HarvestFilter, HarvestFeature
from udata.harvest.exceptions import HarvestSkipException
from udata.models import License, Resource, Organization
from udata.utils import get_by

from urllib.parse import urlparse

def guess_format(mimetype, url=None):
    '''
    Guess a file format given a MIME type and/or an url
    '''
    # TODO: factorize in udata
    ext = mimetypes.guess_extension(mimetype)
    if not ext and url:
        parts = os.path.splitext(url)
        ext = parts[1] if parts[1] else None
    return ext[1:] if ext and ext.startswith('.') else ext


def guess_mimetype(mimetype, url=None):
    '''
    Guess a MIME type given a string or and URL
    '''
    # TODO: factorize in udata
    if mimetype in mimetypes.types_map.values():
        return mimetype
    elif url:
        mime, encoding = mimetypes.guess_type(url)
        return mime


class OdsBackendPT(BaseBackend):
    display_name = 'OpenDataSoft PT'
    verify_ssl = False
    filters = (
        HarvestFilter(_('Tag'), 'tags', str, _('A tag name')),
        HarvestFilter(_('Publisher'), 'publisher', str, _('A publisher name')),
    )
    features = (
        HarvestFeature('inspire', _('Harvest Inspire datasets'),
                       _('Whether this harvester should import datasets coming from Inspire')),
    )

    # Map filters key to ODS facets
    FILTERS = {
        'tags': 'keyword',
        'publisher': 'publisher',
    }

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

    def extra_file_url(self, dataset_id, file_id, plural_type):
        return '{0}/api/datasets/1.0/{1}/{2}/{3}'.format(
            self.source_url, dataset_id, plural_type, file_id
        )

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
            params = {
                'start': count,
                'rows': 50,
                'interopmetas': 'true',
            }
            for f in self.get_filters():
                ods_key = self.FILTERS.get(f['key'], f['key'])
                op = 'exclude' if f.get('type') == 'exclude' else 'refine'
                key = '.'.join((op, ods_key))
                param = params.get(key, set())
                param.add(f['value'])
                params[key] = param
            response = self.get(self.api_url, params=params)
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

        if 'inspire' in ods_interopmetas and not self.has_feature('inspire'):
            msg = 'Dataset {datasetid} has INSPIRE metadata'
            raise HarvestSkipException(msg.format(**ods_dataset))

        dataset = self.get_dataset(item.remote_id)

        dataset.title = ods_metadata['title']
        dataset.frequency = 'unknown'
        description = ods_metadata.get('description', '').strip()
        dataset.description = parse_html(description)
        dataset.private = False

        # Detect Organization
        try:
            organization_acronym = ods_metadata['publisher']
        except KeyError:
            pass
        else:
            orgObj = Organization.objects(acronym=organization_acronym).first()
            if orgObj:
                dataset.organization = orgObj
            else:
                orgObj = Organization()
                orgObj.acronym = organization_acronym
                orgObj.name = organization_acronym
                orgObj.description = organization_acronym
                orgObj.save()

                dataset.organization = orgObj

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

        self.process_extra_files(dataset, ods_dataset, 'alternative_export')
        self.process_extra_files(dataset, ods_dataset, 'attachment')

        dataset.extras['ods:url'] = self.explore_url(dataset_id)
        dataset.extras['harvest:name'] = self.source.name
        
        if 'references' in ods_metadata:
            dataset.extras['ods:references'] = ods_metadata['references']
        dataset.extras['ods:has_records'] = ods_dataset['has_records']
        dataset.extras['ods:geo'] = 'geo' in ods_dataset['features']

        return dataset

    def process_extra_files(self, dataset, data, data_type):
        dataset_id = data['datasetid']
        modified_at = self.parse_date(data['metas']['modified'])
        plural_type = '{0}s'.format(data_type)
        for export in data.get(plural_type, []):
            url = self.extra_file_url(dataset_id, export['id'], plural_type)
            created, resource = self.get_resource(dataset, url)
            resource.title = export.get('title', 'No title')
            resource.description = export.get('description')
            resource.format = guess_format(export.get('mimetype'),
                                           export['url'])
            resource.mime = guess_mimetype(export.get('mimetype'),
                                           export['url'])
            resource.modified = modified_at
            resource.extras['ods:type'] = data_type
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
            resource.extras['ods:type'] = 'api'
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

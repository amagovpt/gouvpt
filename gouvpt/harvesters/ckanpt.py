# Base: udata-ckan
# Version: 1.3.0
# Summary: CKAN integration for udata
# Home-page: https://github.com/opendatateam/udata-ckan

import json
import logging

from datetime import datetime
from uuid import UUID
from urllib.parse import urljoin, urlparse

from voluptuous import (
    Schema, All, Any, Lower, Coerce, DefaultTo, Optional
)

from udata import uris
from udata.i18n import lazy_gettext as _
from udata.core.dataset.rdf import frequency_from_rdf
from udata.frontend.markdown import parse_html
from udata.models import (
    db, Resource, License, SpatialCoverage, GeoZone, Organization, 
    UPDATE_FREQUENCIES,
)
from udata.utils import get_by, daterange_start, daterange_end, safe_unicode

from .tools.harvester_utils import missing_datasets_warning

from udata.harvest.backends.base import BaseBackend, HarvestFilter
from udata.harvest.exceptions import HarvestException, HarvestSkipException
from udata.harvest.filters import (
    boolean, email, to_date, slug, normalize_tag, normalize_string,
    is_url, empty_none, hash
)

from .schemas.ckan import schema as ckan_schema

log = logging.getLogger(__name__)


ALLOWED_RESOURCE_TYPES = ('dkan', 'file', 'file.upload', 'api', 'metadata')


class CkanPTBackend(BaseBackend):
    display_name = 'CKAN PT'
    filters = (
        HarvestFilter(_('Organization'), 'organization', str,
                      _('A CKAN Organization name')),
        HarvestFilter(_('Tag'), 'tags', str, _('A CKAN tag name')),
    )
    schema = ckan_schema

    harvest_config = {}

    def __init__(self, source_or_job, dryrun=False, max_items=None):
        super(CkanPTBackend, self).__init__(source_or_job, dryrun=dryrun, max_items=max_items)
        try:
            self.harvest_config = json.loads(safe_unicode(self.source.description))
        except ValueError as e:
                pass

    def get_headers(self):
        headers = super(CkanPTBackend, self).get_headers()
        headers['content-type'] = 'application/json'
        if self.config.get('apikey'):
            headers['Authorization'] = self.config['apikey']
        return headers

    def action_url(self, endpoint):
        path = '/'.join(['api/3/action', endpoint])
        return urljoin(self.source.url, path)

    def dataset_url(self, name):
        path = '/'.join(['dataset', name])
        return urljoin(self.source.url, path)

    def get_action(self, endpoint, fix=False, **kwargs):
        url = self.action_url(endpoint)
        if fix:
            response = self.post(url, '{}', params=kwargs)
        else:
            response = self.get(url, params=kwargs)

        content_type = response.headers.get('Content-Type', '')
        mime_type = content_type.split(';', 1)[0]

        if mime_type == 'application/json':  # Standard API JSON response
            data = response.json()
            # CKAN API always returns 200 even on errors
            # Only the `success` property allows to detect errors
            if data.get('success', False):
                return data
            else:
                error = data.get('error')
                if isinstance(error, dict):
                    # Error object with message
                    msg = error.get('message', 'Unknown error')
                    if '__type' in error:
                        # Typed error
                        msg = ': '.join((error['__type'], msg))
                else:
                    # Error only contains a message
                    msg = error
                raise HarvestException(msg)

        elif mime_type == 'text/html':  # Standard html error page
            raise HarvestException('Unknown Error: {} returned HTML'.format(url))
        else:
            # If it's not HTML, CKAN respond with raw quoted text
            msg = response.text.strip('"')
            raise HarvestException(msg)

    def get_status(self):
        url = urljoin(self.source.url, '/api/util/status')
        response = self.get(url)
        return response.json()

    def initialize(self):

        try:
            self.harvest_config = json.loads(safe_unicode(self.source.description))
        except ValueError as e:
            if self.dryrun:
                raise e
            else:
                pass

        '''List all datasets for a given ...'''
        fix = False  # Fix should be True for CKAN < '1.8'

        filters = self.config.get('filters', [])
        if len(filters) > 0:
            # Build a q search query based on filters
            # use package_search because package_list doesn't allow filtering
            # use q parameters because fq is broken with multiple filters
            params = []
            for f in filters:
                param = '{key}:{value}'.format(**f)
                if f.get('type') == 'exclude':
                    param = '-' + param
                params.append(param)
            q = ' AND '.join(params)
            response = self.get_action('package_search', fix=fix, q=q, rows=1000)
            names = [r['name'] for r in response['result']['results']]
        else:
            response = self.get_action('package_list', fix=fix)
            names = response['result']
        if self.max_items:
            names = names[:self.max_items]
        for name in names:
            self.add_item(name)

    def process(self, item):
        response = self.get_action('package_show', id=item.remote_id)
        data = self.validate(response['result'], self.schema)

        if type(data) == list:
            data = data[0]

        # Fix the remote_id: use real ID instead of not stable name
        item.remote_id = data['id']

        # Skip if no resource
        if not len(data.get('resources', [])):
            msg = 'Dataset {0} has no record'.format(item.remote_id)
            raise HarvestSkipException(msg)

        dataset = self.get_dataset(item.remote_id)

        # Core attributes
        if not dataset.slug:
            dataset.slug = data['name']
        dataset.title = data['title']
        dataset.description = parse_html(data['notes'])

        # Detect Org
        organization_acronym = data['organization']['name']
        orgObj = Organization.objects(acronym=organization_acronym).first()
        if orgObj:
            #print 'Found %s' % orgObj.acronym
            dataset.organization = orgObj
        else:
            orgObj = Organization()
            orgObj.acronym = organization_acronym
            orgObj.name = data['organization']['title']
            orgObj.description = data['organization']['description']
            orgObj.save()
            #print 'Created %s' % orgObj.acronym

            dataset.organization = orgObj


        # Detect license
        default_license = self.harvest_config.get('license', License.default())
        dataset.license = License.guess(data['license_id'],
                                        data['license_title'],
                                        default=default_license)

        dataset.tags = [t['name'] for t in data['tags'] if t['name']]


        dataset.tags.append(urlparse(self.source.url).hostname)
        
        dataset.created_at = data['metadata_created']
        dataset.last_modified = data['metadata_modified']

        dataset.frequency = 'unknown'
        dataset.extras['ckan:name'] = data['name']

        temporal_start, temporal_end = None, None
        spatial_geom = None

        for extra in data['extras']:
            # GeoJSON representation (Polygon or Point)
            if extra['key'] == 'spatial':
                spatial_geom = json.loads(extra['value'])
            #  Textual representation of the extent / location
            elif extra['key'] == 'spatial-text':
                log.debug('spatial-text value not handled')
            # Linked Data URI representing the place name
            elif extra['key'] == 'spatial-uri':
                log.debug('spatial-uri value not handled')
            # Update frequency
            elif extra['key'] == 'frequency':
                print('frequency', extra['value'])
            # Temporal coverage start
            elif extra['key'] == 'temporal_start':
                temporal_start = daterange_start(extra['value'])
                continue
            # Temporal coverage end
            elif extra['key'] == 'temporal_end':
                temporal_end = daterange_end(extra['value'])
                continue
            dataset.extras[extra['key']] = extra['value']

        # We don't want spatial to be added on harvester
        if self.harvest_config.get('geozones', False):
            dataset.spatial = SpatialCoverage()
            dataset.spatial.zones = []
            for zone in self.harvest_config.get('geozones'):
                geo_zone = GeoZone.objects.get(id=zone)
                dataset.spatial.zones.append(geo_zone)
        #
        # if spatial_geom:
        #     dataset.spatial = SpatialCoverage()
        #     if spatial_geom['type'] == 'Polygon':
        #         coordinates = [spatial_geom['coordinates']]
        #     elif spatial_geom['type'] == 'MultiPolygon':
        #         coordinates = spatial_geom['coordinates']
        #     else:
        #         HarvestException('Unsupported spatial geometry')
        #     dataset.spatial.geom = {
        #         'type': 'MultiPolygon',
        #         'coordinates': coordinates
        #     }

        if temporal_start and temporal_end:
            dataset.temporal_coverage = db.DateRange(
                start=temporal_start,
                end=temporal_end,
            )

        # Remote URL
        if data.get('url'):
            try:
                url = uris.validate(data['url'])
            except uris.ValidationError:
                dataset.extras['remote_url'] = self.dataset_url(data['name'])
                dataset.extras['ckan:source'] = data['url']
            else:
                dataset.extras['remote_url'] = url
        
        dataset.extras['harvest:name'] = self.source.name

        current_resources = [str(resource.id) for resource in dataset.resources]
        fetched_resources = []
        # Resources
        for res in data['resources']:
            if res['resource_type'] not in ALLOWED_RESOURCE_TYPES:
                continue
            
            #Ignore invalid Resources
            try:
                url = uris.validate(res['url'])
            except uris.ValidationError:
                continue            

            try:
                resource = get_by(dataset.resources, 'id', UUID(res['id']))
            except Exception:
                log.error('Unable to parse resource ID %s', res['id'])
                continue
            
            fetched_resources.append(str(res['id']))
            if not resource:
                resource = Resource(id=res['id'])
                dataset.resources.append(resource)
            resource.title = res.get('name', '') or ''
            resource.description = parse_html(res.get('description'))
            resource.url = res['url']
            resource.filetype = 'remote'
            resource.format = res.get('format')
            resource.mime = res.get('mimetype')
            resource.hash = res.get('hash')
            resource.created = res['created']
            resource.modified = res['last_modified']
            resource.published = resource.published or resource.created

        # Clean up old resources removed from source
        for resource_id in current_resources:
            if resource_id not in fetched_resources:
                try:
                    resource = get_by(dataset.resources, 'id', UUID(resource_id))
                except Exception:
                    log.error('Unable to parse resource ID %s', resource_id)
                    continue
                else:
                    if resource and not self.dryrun:
                        dataset.resources.remove(resource)

        return dataset

    def finalize(self):
        super(CkanPTBackend, self).finalize()

        # Check if datasets removed in origin
        if not self.dryrun:
            missing_datasets_warning(job_items=self.job.items, source=self.source)
import json

from datetime import datetime

from flask import url_for
from udata.tests.api import APITestCase

from udata.core.dataset.factories import (
    DatasetFactory, VisibleDatasetFactory, CommunityResourceFactory,
    LicenseFactory, ResourceFactory)
from udata.core.dataset.models import RESOURCE_FILETYPE_FILE, ResourceMixin
from udata.core.user.factories import UserFactory, AdminFactory
from udata.core.badges.factories import badge_factory
from udata.core.organization.factories import OrganizationFactory
from udata.models import (
    CommunityResource, Dataset, Follow, Member, UPDATE_FREQUENCIES,
    LEGACY_FREQUENCIES, RESOURCE_TYPES, db
)
from udata.tags import MIN_TAG_LENGTH, MAX_TAG_LENGTH
from udata.utils import unique_string, faker


SAMPLE_GEOM = {
    "type": "MultiPolygon",
    "coordinates": [
        [[[102.0, 2.0], [103.0, 2.0], [103.0, 3.0], [102.0, 3.0], [102.0, 2.0]]],  # noqa
        [[[100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]],  # noqa
        [[100.2, 0.2], [100.8, 0.2], [100.8, 0.8], [100.2, 0.8], [100.2, 0.2]]]
    ]
}


class DatasetAPITest(APITestCase):
    modules = ['core.user', 'core.dataset', 'core.organization']

    def test_dataset_api_list(self):
        '''It should fetch a dataset list from the API'''
        with self.autoindex():
            datasets = [VisibleDatasetFactory() for i in range(2)]

        response = self.get(url_for('api.datasets'))
        self.assert200(response)
        self.assertEqual(len(response.json['data']), len(datasets))
        self.assertFalse('quality' in response.json['data'][0])

    def test_dataset_api_search(self):
        '''It should search datasets from the API'''
        with self.autoindex():
            [VisibleDatasetFactory() for i in range(2)]
            dataset = VisibleDatasetFactory(title="some spécial chars")

        response = self.get(url_for('api.datasets', q='spécial'))
        self.assert200(response)
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(response.json['data'][0]['id'], str(dataset.id))

    def test_dataset_api_list_filtered_by_org(self):
        '''It should fetch a dataset list for a given org'''
        self.login()
        with self.autoindex():
            member = Member(user=self.user, role='editor')
            org = OrganizationFactory(members=[member])
            VisibleDatasetFactory()
            dataset_org = VisibleDatasetFactory(organization=org)

        response = self.get(url_for('api.datasets'),
                            qs={'organization': str(org.id)})
        self.assert200(response)
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(response.json['data'][0]['id'], str(dataset_org.id))

    def test_dataset_api_list_filtered_by_org_with_or(self):
        '''It should fetch a dataset list for two given orgs'''
        self.login()
        with self.autoindex():
            member = Member(user=self.user, role='editor')
            org1 = OrganizationFactory(members=[member])
            org2 = OrganizationFactory(members=[member])
            VisibleDatasetFactory()
            dataset_org1 = VisibleDatasetFactory(organization=org1)
            dataset_org2 = VisibleDatasetFactory(organization=org2)

        response = self.get(
            url_for('api.datasets'),
            qs={'organization': '{0}|{1}'.format(org1.id, org2.id)})
        self.assert200(response)
        self.assertEqual(len(response.json['data']), 2)
        returned_ids = [item['id'] for item in response.json['data']]
        self.assertIn(str(dataset_org1.id), returned_ids)
        self.assertIn(str(dataset_org2.id), returned_ids)

    def test_dataset_api_list_with_facets(self):
        '''It should fetch a dataset list from the API with facets'''
        with self.autoindex():
            for i in range(2):
                VisibleDatasetFactory(tags=['tag-{0}'.format(i)])

        response = self.get(url_for('api.datasets', **{'facets': 'tag'}))
        self.assert200(response)
        self.assertEqual(len(response.json['data']), 2)
        self.assertIn('facets', response.json)
        self.assertIn('tag', response.json['facets'])

    def test_dataset_api_get(self):
        '''It should fetch a dataset from the API'''
        with self.autoindex():
            resources = [ResourceFactory() for _ in range(2)]
            dataset = DatasetFactory(resources=resources)

        response = self.get(url_for('api.dataset', dataset=dataset))
        self.assert200(response)
        data = json.loads(response.data)
        self.assertEqual(len(data['resources']), len(resources))
        self.assertFalse('quality' in data)

    def test_dataset_api_get_deleted(self):
        '''It should not fetch a deleted dataset from the API and raise 410'''
        dataset = VisibleDatasetFactory(deleted=datetime.now())

        response = self.get(url_for('api.dataset', dataset=dataset))
        self.assert410(response)

    def test_dataset_api_get_deleted_but_authorized(self):
        '''It should a deleted dataset from the API if user is authorized'''
        self.login()
        dataset = VisibleDatasetFactory(owner=self.user,
                                        deleted=datetime.now())

        response = self.get(url_for('api.dataset', dataset=dataset))
        self.assert200(response)

    def test_dataset_api_fail_to_create_too_short_tags(self):
        '''It should fail to create a dataset from the API because
        the tag is too short'''
        data = DatasetFactory.as_dict()
        data['tags'] = [unique_string(MIN_TAG_LENGTH - 1)]
        with self.api_user():
            response = self.post(url_for('api.datasets'), data)
        self.assertStatus(response, 400)

    def test_dataset_api_fail_to_create_too_long_tags(self):
        '''Should fail creating a dataset with a tag long'''
        data = DatasetFactory.as_dict()
        data['tags'] = [unique_string(MAX_TAG_LENGTH + 1)]
        with self.api_user():
            response = self.post(url_for('api.datasets'), data)
        self.assertStatus(response, 400)

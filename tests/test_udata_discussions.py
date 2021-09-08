# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from flask import url_for

from udata.models import Dataset, Member
from udata.core.discussions.models import Message, Discussion
from udata.core.discussions.notifications import discussions_notifications
from udata.core.discussions.signals import (
    on_new_discussion, on_new_discussion_comment,
    on_discussion_closed, on_discussion_deleted,
)
from udata.core.discussions.tasks import (
    notify_new_discussion, notify_new_discussion_comment,
    notify_discussion_closed
)
from udata.core.dataset.factories import DatasetFactory
from udata.core.discussions.factories import DiscussionFactory
from udata.core.organization.factories import OrganizationFactory
from udata.core.user.factories import UserFactory, AdminFactory
from udata.utils import faker


from udata.tests.frontend import FrontTestCase

from udata.tests import TestCase, DBTestMixin
from udata.tests.api import APITestCase
from udata.tests.helpers import assert_starts_with, capture_mails, assert_emit


class DiscussionsTest(APITestCase):
    modules = ['core.user']

    def test_list_discussions(self):
        dataset = Dataset.objects.create(title='Test dataset')
        open_discussions = []
        closed_discussions = []
        for i in range(2):
            user = UserFactory()
            message = Message(content=faker.sentence(), posted_by=user)
            discussion = Discussion.objects.create(
                subject=dataset,
                user=user,
                title='test discussion {}'.format(i),
                discussion=[message]
            )
            open_discussions.append(discussion)
        for i in range(3):
            user = UserFactory()
            message = Message(content=faker.sentence(), posted_by=user)
            discussion = Discussion.objects.create(
                subject=dataset,
                user=user,
                title='test discussion {}'.format(i),
                discussion=[message],
                closed=datetime.now(),
                closed_by=user
            )
            closed_discussions.append(discussion)

        response = self.get(url_for('api.discussions'))
        self.assert200(response)

        self.assertEqual(len(response.json['data']),
                         len(open_discussions + closed_discussions))

    def test_list_discussions_closed_filter(self):
        dataset = Dataset.objects.create(title='Test dataset')
        open_discussions = []
        closed_discussions = []
        for i in range(2):
            user = UserFactory()
            message = Message(content=faker.sentence(), posted_by=user)
            discussion = Discussion.objects.create(
                subject=dataset,
                user=user,
                title='test discussion {}'.format(i),
                discussion=[message]
            )
            open_discussions.append(discussion)
        for i in range(3):
            user = UserFactory()
            message = Message(content=faker.sentence(), posted_by=user)
            discussion = Discussion.objects.create(
                subject=dataset,
                user=user,
                title='test discussion {}'.format(i),
                discussion=[message],
                closed=datetime.now(),
                closed_by=user
            )
            closed_discussions.append(discussion)

        response = self.get(url_for('api.discussions', closed=True))
        self.assert200(response)
        self.assertEqual(len(response.json['data']), len(closed_discussions))
        for discussion in response.json['data']:
            self.assertIsNotNone(discussion['closed'])

    def test_list_discussions_for(self):
        dataset = DatasetFactory()
        discussions = []
        for i in range(3):
            user = UserFactory()
            message = Message(content=faker.sentence(), posted_by=user)
            discussion = Discussion.objects.create(
                subject=dataset,
                user=user,
                title='test discussion {}'.format(i),
                discussion=[message]
            )
            discussions.append(discussion)
        user = UserFactory()
        message = Message(content=faker.sentence(), posted_by=user)
        Discussion.objects.create(
            subject=DatasetFactory(),
            user=user,
            title='test discussion {}'.format(i),
            discussion=[message]
        )

        kwargs = {'for': str(dataset.id)}
        response = self.get(url_for('api.discussions', **kwargs))
        self.assert200(response)

        self.assertEqual(len(response.json['data']), len(discussions))

    def test_get_discussion(self):
        dataset = Dataset.objects.create(title='Test dataset')
        user = UserFactory()
        message = Message(content='bla bla', posted_by=user)
        discussion = Discussion.objects.create(
            subject=dataset,
            user=user,
            title='test discussion',
            discussion=[message]
        )

        response = self.get(url_for('api.discussion', **{'id': discussion.id}))
        self.assert200(response)

        data = response.json

        self.assertEqual(data['subject']['class'], 'Dataset')
        self.assertEqual(data['subject']['id'], str(dataset.id))
        self.assertEqual(data['user']['id'], str(user.id))
        self.assertEqual(data['title'], 'test discussion')
        self.assertIsNotNone(data['created'])
        self.assertEqual(len(data['discussion']), 1)
        self.assertEqual(data['discussion'][0]['content'], 'bla bla')
        self.assertEqual(
            data['discussion'][0]['posted_by']['id'], str(user.id))
        self.assertIsNotNone(data['discussion'][0]['posted_on'])
        

class DiscussionsNotificationsTest(TestCase, DBTestMixin):
    def test_notify_user_discussions(self):
        owner = UserFactory()
        dataset = DatasetFactory(owner=owner)

        open_discussions = {}
        for i in range(3):
            user = UserFactory()
            message = Message(content=faker.sentence(), posted_by=user)
            discussion = Discussion.objects.create(
                subject=dataset,
                user=user,
                title=faker.sentence(),
                discussion=[message]
            )
            open_discussions[discussion.id] = discussion
        # Creating a closed discussion that shouldn't show up in response.
        user = UserFactory()
        message = Message(content=faker.sentence(), posted_by=user)
        discussion = Discussion.objects.create(
            subject=dataset,
            user=user,
            title=faker.sentence(),
            discussion=[message],
            closed=datetime.now(),
            closed_by=user
        )

        notifications = discussions_notifications(owner)

        self.assertEqual(len(notifications), len(open_discussions))

        for dt, details in notifications:
            discussion = open_discussions[details['id']]
            self.assertEqual(details['title'], discussion.title)
            self.assertEqual(details['subject']['id'], discussion.subject.id)
            self.assertEqual(details['subject']['type'], 'dataset')

    def test_notify_org_discussions(self):
        recipient = UserFactory()
        member = Member(user=recipient, role='editor')
        org = OrganizationFactory(members=[member])
        dataset = DatasetFactory(organization=org)

        open_discussions = {}
        for i in range(3):
            user = UserFactory()
            message = Message(content=faker.sentence(), posted_by=user)
            discussion = Discussion.objects.create(
                subject=dataset,
                user=user,
                title=faker.sentence(),
                discussion=[message]
            )
            open_discussions[discussion.id] = discussion
        # Creating a closed discussion that shouldn't show up in response.
        user = UserFactory()
        message = Message(content=faker.sentence(), posted_by=user)
        discussion = Discussion.objects.create(
            subject=dataset,
            user=user,
            title=faker.sentence(),
            discussion=[message],
            closed=datetime.now(),
            closed_by=user
        )

        notifications = discussions_notifications(recipient)

        self.assertEqual(len(notifications), len(open_discussions))

        for dt, details in notifications:
            discussion = open_discussions[details['id']]
            self.assertEqual(details['title'], discussion.title)
            self.assertEqual(details['subject']['id'], discussion.subject.id)
            self.assertEqual(details['subject']['type'], 'dataset')


class DiscussionsMailsTest(FrontTestCase):
    modules = ['core.user', 'core.dataset']

    def test_new_discussion_mail(self):
        user = UserFactory()
        owner = UserFactory()
        message = Message(content=faker.sentence(), posted_by=user)
        discussion = Discussion.objects.create(
            subject=DatasetFactory(owner=owner),
            user=user,
            title=faker.sentence(),
            discussion=[message]
        )

        with capture_mails() as mails:
            notify_new_discussion(discussion)

        # Should have sent one mail to the owner
        self.assertEqual(len(mails), 1)
        self.assertEqual(mails[0].recipients[0], owner.email)

    def test_new_discussion_comment_mail(self):
        owner = UserFactory()
        poster = UserFactory()
        commenter = UserFactory()
        message = Message(content=faker.sentence(), posted_by=poster)
        new_message = Message(content=faker.sentence(), posted_by=commenter)
        discussion = Discussion.objects.create(
            subject=DatasetFactory(owner=owner),
            user=poster,
            title=faker.sentence(),
            discussion=[message, new_message]
        )

        with capture_mails() as mails:
            notify_new_discussion_comment(discussion, message=new_message)

        # Should have sent one mail to the owner and the other participants
        # and no mail to the commenter
        expected_recipients = (owner.email, poster.email)
        self.assertEqual(len(mails), len(expected_recipients))
        for mail in mails:
            self.assertIn(mail.recipients[0], expected_recipients)
            self.assertNotIn(commenter.email, mail.recipients)

    def test_closed_discussion_mail(self):
        owner = UserFactory()
        poster = UserFactory()
        commenter = UserFactory()
        message = Message(content=faker.sentence(), posted_by=poster)
        second_message = Message(content=faker.sentence(), posted_by=commenter)
        closing_message = Message(content=faker.sentence(), posted_by=owner)
        discussion = Discussion.objects.create(
            subject=DatasetFactory(owner=owner),
            user=poster,
            title=faker.sentence(),
            discussion=[message, second_message, closing_message]
        )

        with capture_mails() as mails:
            notify_discussion_closed(discussion, message=closing_message)

        # Should have sent one mail to each participant
        # and no mail to the closer
        expected_recipients = (poster.email, commenter.email)
        self.assertEqual(len(mails), len(expected_recipients))
        for mail in mails:
            self.assertIn(mail.recipients[0], expected_recipients)
            self.assertNotIn(owner.email, mail.recipients)
